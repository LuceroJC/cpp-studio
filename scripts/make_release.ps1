param(
  [string]$Version = "0.1.0",
  [switch]$IncludeAudio = $false,
  [string]$Suffix = "windows"
)

# Build the release folder name once, honoring the (optional) suffix
$ReleaseName = "cpp-studio-$Version" + ($(if ($Suffix) { "-$Suffix" } else { "" }))
$tagDir = Join-Path -Path "releases" -ChildPath $ReleaseName

$ErrorActionPreference = "Stop"

# 1) Ensure clean venv tools
python -m pip install --upgrade pip build

# 2) Build wheel + sdist
python -m build

# 3) Create dirs (DO NOT overwrite $tagDir)
$null = New-Item -ItemType Directory -Force -Path $tagDir
$distOut  = Join-Path $tagDir "dist"
$docsOut  = Join-Path $tagDir "docs"
$cliOut   = Join-Path $tagDir "cli"
$praatOut = Join-Path $tagDir "praat"
$dataOut  = Join-Path $tagDir "data_sample"
New-Item -ItemType Directory -Force -Path $distOut,$docsOut,$cliOut,$praatOut,$dataOut | Out-Null

# 4) Copy dist artifacts
Copy-Item dist\*.whl $distOut
Copy-Item dist\*.tar.gz $distOut

# 5) Copy docs & scripts
Copy-Item LICENSE $tagDir
Copy-Item docs\README.md $docsOut
Copy-Item praat\cpps_*.praat $praatOut
Copy-Item cli\run_cpps.py, cli\report.py $cliOut

# 6) Attribution file (use a here-string)
@"
This sample pack includes audio derived from the VOICED Database (v1.0.0), PhysioNet.
Source: VOICED Database — Laura Verde, Giovanna Sannino (2018).
Access policy: Open Access. License: Open Data Commons Attribution (ODC-By) v1.0.
Dataset DOI: https://doi.org/10.13026/C25Q2N
PhysioNet record: https://physionet.org/content/voiced/1.0.0/
Please cite both:
1) Cesari U. et al., 'A new database of healthy and pathological voices,' Computers & Electrical Engineering, 68:310–321, 2018.
2) Goldberger A.L. et al., 'PhysioBank, PhysioToolkit, and PhysioNet,' Circulation, 101(23):e215–e220, 2000.
"@ | Set-Content -Encoding UTF8 (Join-Path $docsOut "ATTRIBUTION.txt")

# 7) Data sample
Copy-Item data_sample\MANIFEST.csv $dataOut
Copy-Item data_sample\ATTRIBUTION.txt $dataOut -ErrorAction SilentlyContinue
if ($IncludeAudio) {
  # If you use Git LFS, ensure 'git lfs pull' ran before copying.
  Copy-Item data_sample\*.wav $dataOut -ErrorAction SilentlyContinue
}

# 8) RUNME
@"
CPP Studio v$Version — quick start
==================================

1) Create a virtual environment and install the wheel:
   python -m venv .venv
   .\.venv\Scripts\activate
   python -m pip install --upgrade pip
   python -m pip install dist\cpp_studio-$Version-py3-none-any.whl

2) (Optional) Verify console scripts:
   cpps-run --help
   cpps-report --help

3) Reproduce the paper-ready PDF (Praat-match + per-frame):
   cpps-run .\data_sample --praat-match --per_frame --out cpps_summary_praat_match.csv
   cpps-report --summary cpps_summary_praat_match.csv --out cpps_batch_report.pdf --paper a4 --margins 0.6 --title "CPP Studio"

Notes:
- Per-frame outputs are saved as *_cpps_framewise.csv and PNGs under frame_plots/.
- This software is for research/education; not a medical device.
"@ | Set-Content -Encoding UTF8 (Join-Path $tagDir "RUNME.txt")

# 9) Checksums  (files only; relative paths)
Set-Location $tagDir
Get-ChildItem -Recurse -File |
  Where-Object { $_.Name -ne 'CHECKSUMS.txt' } |
  Get-FileHash -Algorithm SHA256 |
  ForEach-Object {
    $rel = (Resolve-Path -Relative $_.Path)
    "{0}  {1}" -f $_.Hash, $rel
  } | Set-Content -Encoding ASCII "CHECKSUMS.txt"
Set-Location -

Write-Host "Release directory created: $tagDir"
