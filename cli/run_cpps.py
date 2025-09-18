import argparse
import json
from pathlib import Path
from cli.cpps import compute_cpps_batch


parser = argparse.ArgumentParser(description="CPP Studio — batch CPPS/CPP analyzer")
parser.add_argument("inputs", nargs="+", help="WAV files or a folder containing WAVs")
parser.add_argument("--frame_ms", type=int, default=40)
parser.add_argument("--hop_pct", type=int, default=50)
parser.add_argument("--preemph_alpha", type=float, default=0.97)
parser.add_argument("--f0_min", type=int, default=60)
parser.add_argument("--f0_max", type=int, default=500)
parser.add_argument("--energy_gate_db", type=int, default=25)
parser.add_argument("--med_smooth_frames", type=int, default=3)
parser.add_argument("--per_frame", action="store_true", help="Save per‑frame CSVs")
parser.add_argument("--out", default="cpps_summary.csv")


if __name__ == "__main__":
args = parser.parse_args()
files = []
for inp in args.inputs:
p = Path(inp)
if p.is_dir():
files += [str(f) for f in p.glob("*.wav")]
else:
files.append(str(p))


df, per_frame = compute_cpps_batch(
files,
frame_ms=args.frame_ms,
hop_pct=args.hop_pct,
preemph_alpha=args.preemph_alpha,
f0_min=args.f0_min,
f0_max=args.f0_max,
energy_gate_db=args.energy_gate_db,
med_smooth_frames=args.med_smooth_frames,
return_per_frame=args.per_frame,
)
df.to_csv(args.out, index=False)


if args.per_frame:
for path, pf in per_frame.items():
pf.to_csv(f"{Path(path).stem}_perframe.csv", index=False)


print(f"Wrote {args.out} with {len(df)} files.")