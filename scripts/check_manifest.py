import sys, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
data_dir = ROOT / "data_sample"
manifest = ROOT / "data_sample" / "MANIFEST.csv"

errors = []

if not manifest.exists():
    print("ERROR: data_sample/MANIFEST.csv not found.")
    sys.exit(1)

df = pd.read_csv(manifest)

# Expect a 'file' column with relative paths or filenames
if "file" not in df.columns:
    print("ERROR: MANIFEST.csv must contain a 'file' column.")
    sys.exit(1)

# Normalize both sides to bare filenames for lenient matching
listed = {pathlib.Path(str(x)).name for x in df["file"].dropna().astype(str).tolist()}
on_disk = {p.name for p in data_dir.glob("*.wav")}

missing = sorted(listed - on_disk)
extra   = sorted(on_disk - listed)

if missing:
    errors.append(f"Listed but missing on disk: {len(missing)}\n  - " + "\n  - ".join(missing))
if extra:
    errors.append(f"Present on disk but not listed: {len(extra)}\n  - " + "\n  - ".join(extra))

if errors:
    print("Manifest check failed:\n" + "\n\n".join(errors))
    sys.exit(1)

print(f"Manifest OK: {len(on_disk)} WAVs match MANIFEST.csv")
