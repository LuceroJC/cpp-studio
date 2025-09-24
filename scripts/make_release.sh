#!/usr/bin/env bash
set -euo pipefail

VER=${1:-0.1.0}           # version, e.g., 0.1.0
INCLUDE_AUDIO=${2:-false} # true|false — copy data_sample/*.wav (requires LFS pull)
SUFFIX=${3:-linux}        # suffix so we don't clobber the Windows bundle

# Ensure build tooling is present
python3 -m pip install --upgrade --user pip build
python3 -m build

RELEASENAME="cpp-studio-${VER}-${SUFFIX}"
TAGDIR="releases/${RELEASENAME}"

# Layout
mkdir -p "${TAGDIR}/dist" "${TAGDIR}/docs" "${TAGDIR}/cli" "${TAGDIR}/praat" "${TAGDIR}/data_sample"

# dist
cp -v dist/*.whl dist/*.tar.gz "${TAGDIR}/dist/"

# docs & scripts
cp -v LICENSE "${TAGDIR}/"
cp -v docs/README.md "${TAGDIR}/docs/"  # your main docs live here
cp -v cli/run_cpps.py cli/report.py "${TAGDIR}/cli/"
cp -v praat/cpps_*.praat "${TAGDIR}/praat/" 2>/dev/null || true

# attribution text
cat > "${TAGDIR}/docs/ATTRIBUTION.txt" << 'TXT'
This sample pack includes audio derived from the VOICED Database (v1.0.0), PhysioNet.
Source: VOICED Database — Laura Verde, Giovanna Sannino (2018).
Access policy: Open Access. License: Open Data Commons Attribution (ODC-By) v1.0.
Dataset DOI: https://doi.org/10.13026/C25Q2N
PhysioNet record: https://physionet.org/content/voiced/1.0.0/
Please cite both:
1) Cesari U. et al., "A new database of healthy and pathological voices," Computers & Electrical Engineering, 68:310–321, 2018.
2) Goldberger A.L. et al., "PhysioBank, PhysioToolkit, and PhysioNet," Circulation, 101(23):e215–e220, 2000.
TXT

# sample data (manifest + attribution + optional audio)
cp -v data_sample/MANIFEST.csv "${TAGDIR}/data_sample/" 2>/dev/null || true
[ -f data_sample/ATTRIBUTION.txt ] && cp -v data_sample/ATTRIBUTION.txt "${TAGDIR}/data_sample/"
if [ "${INCLUDE_AUDIO}" = "true" ]; then
  # Ensure 'git lfs pull' ran if WAVs are tracked via LFS
  cp -v data_sample/*.wav "${TAGDIR}/data_sample/" 2>/dev/null || true
fi

# RUNME
cat > "${TAGDIR}/RUNME.txt" << RUN
CPP Studio v${VER} — quick start
================================

1) Create a virtual environment and install the wheel:
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install dist/cpp_studio-${VER}-py3-none-any.whl

2) (Optional) Verify console scripts:
   cpps-run --help
   cpps-report --help

3) Reproduce the paper-ready PDF (Praat-match + per-frame):
   cpps-run ./data_sample --praat-match --per_frame --out cpps_summary_praat_match.csv
   cpps-report --summary cpps_summary_praat_match.csv --out cpps_batch_report.pdf --paper a4 --margins 0.6 --title "CPP Studio"

Notes:
- Per-frame outputs are saved as *_cpps_framewise.csv and PNGs under frame_plots/.
- This software is for research/education; not a medical device.
RUN

# CHECKSUMS (relative paths)
( cd "${TAGDIR}" && find . -type f ! -name 'CHECKSUMS.txt' -print0 \
    | xargs -0 sha256sum > CHECKSUMS.txt )

echo "Release directory created: ${TAGDIR}"
