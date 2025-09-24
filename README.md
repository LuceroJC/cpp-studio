# CPP Studio — CPPS/CPP Batch Analyzer (v0.1.0)

[![CI](https://github.com/lucerojc/cpp-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/lucerojc/cpp-studio/actions/workflows/ci.yml)

Practical **Cepstral Peak Prominence (Smoothed)** analysis for clinics, research, and teaching. Batch WAV → **CSV + per‑frame (optional) + one‑page PDF**. Includes **Praat‑aligned mode** and **Streamlit UI**.

> ⚠️ Not a diagnostic device. Use for measurement/documentation only.

---

## TL;DR — Quick Start

### Run via Docker (no host setup)

**Slim** (no LaTeX; use for analysis and UI):

```bash
# http://localhost:8501
docker run --rm -p 8501:8501 -v "$PWD:/work" -v "$PWD/data_sample:/data" -w /work ghcr.io/lucerojc/cpp-studio:slim \
  streamlit run app/streamlit_app.py --server.headless=true --browser.gatherUsageStats=false
```

**Full** (includes LaTeX to build the PDF inside the container):

```bash
docker run --rm -p 8502:8501 -v "$PWD:/work" -v "$PWD/data_sample:/data" -w /work ghcr.io/lucerojc/cpp-studio:full \
  cpps-report --summary cpps_summary.csv --out cpps_batch_report.pdf --paper a4 --margins 0.6
```

### One‑liners (local install)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e .
cpps-run ./data_sample --praat-match --per_frame --out cpps_summary.csv
cpps-report --summary cpps_summary.csv --out cpps_batch_report.pdf --paper a4 --margins 0.6 --title "CPP Studio"
```

---

## Install Options

### 1) Windows Installer (recommended for clinicians)

Download `cpp-studio-0.1.0-setup.exe` from the GitHub Release and run it. It installs:

* Start‑Menu app **“CPP Studio”** (Streamlit UI)
* CLI tools: `cpps-run` and `cpps-report`

### 2) Pip (developers & CI)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e .    # or: python -m pip install .
```

### 3) Docker Compose (slim by default, full on port 8502)

`compose.yaml` defines two services:

* **app** (slim) → maps **8501:8501**
* **app-full** (LaTeX) → maps **8502:8501**

Commands:

```bash
# Slim UI at http://localhost:8501
docker compose up --build

# Full (LaTeX) UI at http://localhost:8502
docker compose --profile full up --build

# One‑off CLI runs
docker compose run --rm app cpps-run data_sample --praat-match --per_frame --out cpps_summary.csv
docker compose run --rm --profile full app-full \
  cpps-report --summary cpps_summary.csv --out cpps_batch_report.pdf --paper a4 --margins 0.6
```

> If you see a port clash, stop the other service: `docker compose down --remove-orphans`.

---

## Features

* **Praat‑aligned mode (Python)**: Hann 40 ms / 20 ms hop, pre‑emphasis from 50 Hz, power cepstrum, exponential‑decay robust trend, CPP in dB.
* **F0 extraction**: per‑frame F0 from cepstral peak + mean F0.
* **Batch CLI**: `cpps-run` with `--praat-match`, `--praat-bias-db <dB>`, `--per_frame` (saves `*_cpps_framewise.csv` + PNG time‑courses).
* **Report CLI**: `cpps-report` generates a one‑page A4/Letter PDF; handles missing F0.
* **Streamlit UI**: upload/process folders, saves all PNGs and optional per‑frame CSVs to a chosen folder.
* **Praat scripts**: `praat/cpps_slice.praat` (spot check), `praat/cpps_batch.praat` (CSV). Tokens/settings validated.

---

## Outputs

* `cpps_summary_*.csv` — one row per file: mean/median CPPS (dB), % voiced frames, **mean F0 (Hz)**, #frames, duration.
* `*_cpps_framewise.csv` — time‑stamped per‑frame CPPS (and F0 when available).
* `frame_plots/*.png` — per‑file time‑course plots (when `--per_frame`).
* `cpps_batch_report.pdf` — publication‑ready one‑pager (A4 default).

---

## Method details

### Original (Python) path

* Window **Hamming 40 ms**, hop **50 %**, pre‑emphasis **α = 0.97**
* Cepstrum baseline via linear trend; optional median smoothing (`--med_smooth_frames`, default 3)
* Energy gate: skip frames > **25 dB** below file RMS

### Praat‑match path

* **Hann 40 ms**, **20 ms hop**; pre‑emphasis **from 50 Hz**
* **Power cepstrum** of log power spectrum; trend = **Exponential decay** (robust/slow)
* **CPP** = (peak − trend at peak) in **dB** (8.6859× ln)
* **F0** from **cepstral peak quefrency** (F0 = 1/qₚ)
* Optional numeric nudge to match Praat: `--praat-bias-db <dB>`

---

## CLI reference (common flags)

```text
--praat-match                    Use Praat‑aligned method
--praat-bias-db <dB>             Constant offset added to CPPS (Praat‑match only)
--per_frame                      Save per‑frame CSVs + PNG plots
--f0_min <Hz> --f0_max <Hz>      F0 range (default 60–500 Hz)
--paper a4|letter                For PDF layout (report CLI)
--margins <inches>               PDF margins (report CLI)
```

---

## Sample data

Small **healthy VOICED subset** for reproducible testing.

```
data_sample/
  MANIFEST.csv        # voiced_id,file,diagnosis  (all = healthy)
  *.wav               # audio (consider Git LFS)
```

Keep `data_sample/ATTRIBUTION.txt` and cite VOICED/PhysioNet if you redistribute.

---

## Troubleshooting

* **Port already in use (8501)**: stop other service (`docker compose down`) or use full on 8502.
* **Windows Defender flags PyInstaller build**: add exclusions for `dist/` & `build/` or build on CI.
* **`libsndfile` not found**: ensure the Docker image includes `libsndfile1` (it does), or on pip installs use wheels that bundle it. The Windows installer ships the DLL.
* **Matplotlib cache error**: we set `MPLCONFIGDIR` at runtime in the frozen app; for pip installs, delete `%USERPROFILE%\.matplotlib` if permissions block.

---

## Privacy & licensing

* Processes audio **locally**; no cloud upload required.
* Docker Desktop/Podman are third‑party tools; users are responsible for their licenses/policies. Organizations that cannot use Docker Desktop can run images on Linux with Docker Engine or Podman.
* See `LICENSE` and `docs/EULA.md`.

---

## Cite

If CPP Studio helps your work, please cite CPPS/CPP literature and this tool. (Add citation text here.)

---

## Changelog

See `CHANGELOG.md`. Current: **v0.1.0**.
