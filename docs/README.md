# CPP Studio — CPPS/CPP Batch Analyzer (v0.1.0)

[![CI](https://github.com/lucerojc/cpp-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/lucerojc/cpp-studio/actions/workflows/ci.yml)

**Purpose:** Practical measurement & visualization of **Cepstral Peak Prominence (Smoothed)** for voice science, clinics, and labs. **Not a diagnostic device.**

---

## What’s included

* **Python CLI**: batch CPPS/CPP over WAV folders → CSV summary (+ optional per‑frame CSV) and a one‑page **PDF**.
* **Praat‑aligned mode**: reproduces typical Praat defaults (Hann 40/20, pre‑emphasis from 50 Hz, exponential‑decay robust trend). Now also outputs **F0** (from cepstral peak location) per‑frame and as a mean.
* **Praat scripts**: spot check and batch‑to‑CSV for verification.
* **Optional UI**: Streamlit app under `app/` (for non‑sensitive audio only).

---

## Install (offline, recommended)

### Option A — Editable install (preferred)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e .
```

### Option B — Requirements only

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
```

> Tip (Windows): prefer `python -m pip ...` inside the venv to avoid path mix‑ups.

---

## Quick start (CLI)

### Run batch analysis

```bash
# Original method
cpps-run ./wav --out cpps_summary_python.csv

# Praat‑aligned (no bias)
cpps-run ./wav --praat-match --out cpps_summary_praat_match.csv

# Praat‑aligned + numeric nudge (e.g., +6.83 dB to match your Praat build)
cpps-run ./wav --praat-match --praat-bias-db 6.83 --out cpps_summary_praat_match_bias.csv

# Per‑frame exports (adds *_cpps_framewise.csv + PNG plots in ./frame_plots)
cpps-run ./wav --per_frame
```

### Build the one‑page PDF

```bash
cpps-report --summary cpps_summary_praat_match.csv \
  --out cpps_batch_report.pdf --paper a4 --margins 0.6 --title "CPP Studio"
```

**Outputs**

* `cpps_summary_*.csv` — one row per file: mean/median CPPS (dB), **% voiced frames**, **mean F0 (Hz)**, #frames, duration.
* `*_cpps_framewise.csv` — time‑stamped per‑frame CPPS (and F0 when available).
* `frame_plots/*.png` — time‑course plots per file (when `--per_frame`).
* `cpps_batch_report.pdf` — publication‑ready one‑pager (A4 by default).

---

## Defaults & method notes

### Original (Python) path

* Window **Hamming 40 ms**, hop **50 %**, pre‑emphasis **α = 0.97**.
* Cepstrum baseline via linear trend; optional median smoothing (`--med_smooth_frames`, default 3).
* Energy gate: skip frames > **25 dB** below file RMS.

### Praat‑match path

* **Hann 40 ms** window, **20 ms hop**.
* Pre‑emphasis **from 50 Hz**.
* **Power cepstrum** of log power spectrum.
* Trend: **Exponential decay** (robust/slow via IRLS with Huber weights).
* **CPP** = (peak − trend at peak) × **8.6859 dB** (ln→dB).
* **F0** estimated from **cepstral peak quefrency** (F0 = 1/q\_peak). Report includes per‑frame F0 and mean F0 in Praat‑match mode.

> If your Praat build yields a consistent offset, use `--praat-bias-db` to nudge Python outputs to match (document the value you choose).

---

## Praat scripts (validated on 6.4.43)

**Single‑file spot check:** `praat/cpps_slice.praat`

* Per frame: Sound → Spectrum → **To PowerCepstrum** → **Smooth** (0.0015 s, 1 iter)
* Query (exact tokens):

  ```
  Get peak prominence: f0min, f0max, "parabolic", qmin, qmax, "Exponential decay", "Robust slow"
  ```
* Quefrency window auto‑clamped to frame length; frames >20 dB below file RMS are skipped.

**Batch to CSV:** `praat/cpps_batch.praat`

* Walks a folder of WAVs → `cpps_praat_summary.csv` with `file, mean_cpps_db, n_frames`.
* Hanning 40 ms frames, 20 ms hop (configurable), pre‑emphasis from 50 Hz.

Example run:

```
Praat → Open Praat script… → praat/cpps_batch.praat
in_dir=…/wav , out_csv=cpps_praat_summary.csv , f0min=60 , f0max=500
```

---

## Parameters (summary)

* `--frame_ms` (default **40**), `--hop_pct` (default **50**) — original path.
* `--praat-match` (boolean) — switch to Praat‑aligned method.
* `--hop-ms` (default **20**) — hop in Praat‑match mode.
* `--preemph_alpha` (default **0.97**) — original pre‑emph; Praat‑match uses `preemph_from_hz=50` internally.
* `--f0_min`, `--f0_max` (defaults **60–500 Hz**).
* `--energy_gate_db` (default **25 dB** below file RMS).
* `--per_frame` — write per‑frame CSV + PNG plots (to `frame_plots/`).
* `--praat-bias-db` — constant dB offset added to CPPS values (Praat‑match only).

---

## Web demo (optional)

Deploy `app/streamlit_app.py` on Streamlit Cloud/HF Spaces for quick trials. **Do not** upload PHI; use the offline CLI for anything sensitive.

---

## Privacy & compliance

* Processes audio locally when run offline; no cloud upload required.
* This software is for **measurement and documentation**; it is **not** a medical device.

---

## License & citation

* License: see `LICENSE` / `docs/EULA.md` as applicable.
* Please cite relevant CPPS/CPP literature and tools when publishing.

---

## Reproduce the paper‑ready PDF

From a folder of WAVs (e.g., a tiny sample under `data_sample/`):

```bash
cpps-run ./data_sample --praat-match --per_frame --out cpps_summary_praat_match.csv
cpps-report --summary cpps_summary_praat_match.csv --out cpps_batch_report.pdf --paper a4 --margins 0.6 --title "CPP Studio"
```

---


## Sample data in this repo (healthy VOICED subset)

This repository **includes a small set of 30 “healthy” WAV files** derived from the VOICED database (PhysioNet). They are provided for **reproducible benchmarking and screenshots**.

- Source: VOICED Database (PhysioNet, Open Access)
- License: **Open Data Commons Attribution (ODC-By) v1.0**
- Redistribution: permitted **with attribution** to the original authors and PhysioNet
- PHI: none included

If you reuse or redistribute the audio, please keep `data_sample/ATTRIBUTION.txt` (example below) and cite the VOICED paper + PhysioNet.

<details>
<summary><code>data_sample/ATTRIBUTION.txt</code> (template)</summary>

This sample pack includes audio derived from the VOICED Database (v1.0.0), PhysioNet.

Source: VOICED Database — Laura Verde, Giovanna Sannino (2018).  
Access policy: Open Access. License: Open Data Commons Attribution (ODC-By) v1.0.  
Dataset DOI: https://doi.org/10.13026/C25Q2N  
PhysioNet record: https://physionet.org/content/voiced/1.0.0/

Please cite both:
1) Cesari U. et al., “A new database of healthy and pathological voices,” *Computers & Electrical Engineering*, 68:310–321, 2018.  
2) Goldberger A.L. et al., “PhysioBank, PhysioToolkit, and PhysioNet,” *Circulation*, 101(23):e215–e220, 2000.

</details>

### Folder structure

```

data\_sample/
MANIFEST.csv         # voiced\_id,file,diagnosis   (all = healthy)
\*.wav                # your distributed WAV files

````

---

## Reproduce the batch CSV + one-page PDF

> Works with either your sample data in `data_sample/` or any folder of WAV files.

### Bash / macOS / Linux
```bash
# 1) Run Praat-aligned analysis (per-frame outputs + PNG plots)
cpps-run ./data_sample --praat-match --per_frame --out cpps_summary_praat_match.csv

# 2) Build the A4 one-page PDF
cpps-report --summary cpps_summary_praat_match.csv \
  --out cpps_batch_report.pdf --paper a4 --margins 0.6 --title "CPP Studio"
````

### Windows (PowerShell)

```powershell
# 1) Praat-aligned analysis with per-frame outputs
cpps-run .\data_sample --praat-match --per_frame --out cpps_summary_praat_match.csv

# 2) One-page PDF (A4, 0.6in margins)
cpps-report --summary cpps_summary_praat_match.csv `
  --out cpps_batch_report.pdf --paper a4 --margins 0.6 --title "CPP Studio"
```

**Notes**

* `--praat-match` uses Hann 40/20, pre-emphasis from 50 Hz, exponential-decay robust trend; **F0** is estimated from the cepstral peak and included in the report.
* If your Praat build shows a consistent numeric offset vs Python, you can nudge with `--praat-bias-db 6.83` (example value).
* Per-frame CSVs are written as `*_cpps_framewise.csv`; time-course plots go to `frame_plots/`.

## Changelog

See `CHANGELOG.md` for version history. Current: **v0.1.0**.
