# CPP Studio — CPPS/CPP Batch Analyzer (v0.1)

**Purpose:** Measurement & visualization of Cepstral Peak Prominence (Smoothed) for research/education/measurement workflows in clinics and labs. **Not a diagnostic device.**

## Quick Start (Offline CLI)
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m cli.run_cpps path/to/folder --per_frame --out cpps_summary.csv
````

## Quick Start (Web Demo)

* Deploy `app/streamlit_app.py` on Hugging Face Spaces or Streamlit Cloud.
* Web demo is for non‑sensitive audio. Prefer offline CLI for PHI.

## Outputs

* `cpps_summary.csv`: mean/median CPPS (dB), % voiced frames, mean F0, frames, duration.
* Per‑frame CSVs (optional), PNG/SVG plots per file, one‑page PDF/TeX report template under `reports/`.

## Parameters

* Frame length (ms): default 40; Hop (%): 50; Pre‑emphasis α: 0.97; F0 range 60–500 Hz; Energy gate: 25 dB below file RMS; Median smoothing: 3 frames.

## Limitations

* Simplified CPPS estimation; not identical to every reference implementation.
* Sensitive to extreme noise/clipping; review plots and per‑frame data.

## Privacy & Compliance

* Use offline package for PHI. Web demo should not store audio. See `PRIVACY.md`.

## License & Support

* See `EULA.md` for end‑user license. Email support included for 12 months.