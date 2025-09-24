# Calibrating the CPPS bias vs. Praat

This note shows how to estimate a constant dB bias so that `cpps-run --praat-match`
numerically aligns with your local Praat setup for a given dataset.

> TL;DR: run both tools on the same WAVs, join by filename, fit
> `CPP_python ≈ CPP_praat + bias_dB`, then use `--praat-bias-db bias_dB`.

---

## Why a bias?
Praat and our Python impl are aligned on:
- 40 ms Hann window, 20 ms hop
- pre-emphasis from 50 Hz
- power cepstrum, exp-decay robust trend
- CPP in dB

In practice, small implementation details (FFT len, padding, interpolation) can
create a near-constant offset across files. We expose `--praat-bias-db` to absorb it.

---

## Quick recipe

1. **Prepare a file list**
   Put your WAVs under `my_data/`. Optional: use the provided sample set in `data_sample/`.

2. **Run Praat batch**
   Use our helper script (`praat/cpps_batch.praat`) to produce a CSV:
```

# From repo root; adjust Praat app path if needed

"C:/Program Files/Praat/Praat.exe" --run praat/cpps\_batch.praat my\_data praat\_out.csv

```
Columns expected: `file, cpp_db` (+ optional per-frame CPP columns if you enabled them).

3. **Run Python CPPS**
```

cpps-run my\_data --praat-match --out py\_out.csv

```
This writes a per-file summary CSV with `cpp_db` (and `mean_f0_hz` if available).

4. **Join and compute bias**
```

python - <<'PY'
import pandas as pd
pp = pd.read\_csv("praat\_out.csv")
py = pd.read\_csv("py\_out.csv")

# normalize filename keys

pp\['key'] = pp\['file'].str.replace(r'\\|/', '/', regex=True).str.split('/').str\[-1]
py\['key'] = py\['file'].str.replace(r'\\|/', '/', regex=True).str.split('/').str\[-1]
df = pp.merge(py, on='key', suffixes=('\_praat','\_py'))
df = df\[\['key','cpp\_db\_praat','cpp\_db\_py']].dropna()

bias = (df\['cpp\_db\_praat'] - df\['cpp\_db\_py']).median()
mad  = (df\['cpp\_db\_praat'] - df\['cpp\_db\_py']).mad()
print(f"Recommended --praat-bias-db: {bias:+.2f} dB (robust median); MAD={mad:.2f} dB")
print("Preview (first 10):")
print((df\['cpp\_db\_praat'] - df\['cpp\_db\_py']).head(10).to\_string(index=False))
PY

```

5. **Use the bias**
Re-run with:
```

cpps-run my\_data --praat-match --praat-bias-db \<BIAS\_DB> --out py\_out\_bias.csv

```

---

## Reporting your calibration

Include these in your lab notebook / README:

- Date, Praat version, OS
- Python version, `cpp-studio` version/commit
- Dataset description (N speakers, task)
- The bias estimate (median) and dispersion (MAD or SD)
- Plots: a) Bland–Altman, b) scatter with identity line

Example (optional) one-liners:

```

# Bland–Altman

python - <<'PY'
import pandas as pd, matplotlib.pyplot as plt
df = pd.read\_csv("joined.csv")  # save the merged df if you want
d = df\['cpp\_db\_praat'] - df\['cpp\_db\_py']
m = (df\['cpp\_db\_praat'] + df\['cpp\_db\_py'])/2
plt.figure(); plt.scatter(m, d, alpha=0.6)
plt.axhline(d.mean(), linestyle='--')
plt.title("CPP: Praat - Python (Bland–Altman)"); plt.xlabel("Mean (dB)"); plt.ylabel("Diff (dB)")
plt.savefig("calibration\_bland\_altman.png", dpi=200, bbox\_inches="tight")
PY

```

---

## FAQ

- **Should I refit per microphone / room?**  
  If acquisition chains differ substantially, re-check the bias. Often the offset is stable for a given analysis stack.

- **Why median instead of mean?**  
  The median resists occasional outliers from tracking errors or corrupted files.

- **What magnitude should I expect?**  
  Typically within ±0.5 dB if everything is tightly aligned; ±1 dB is still acceptable if dispersion is small.