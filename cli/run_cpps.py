# cli/run_cpps.py
import argparse
import os
from pathlib import Path
from cli.cpps import compute_cpps_batch, save_timecourse_plot

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CPP Studio — batch CPPS/CPP analyzer")
    p.add_argument("inputs", nargs="+", help="WAV files or a folder containing WAVs")

    # Core analysis knobs (original path)
    p.add_argument("--frame_ms", type=int, default=40)
    p.add_argument("--hop_pct", type=int, default=50)
    p.add_argument("--preemph_alpha", type=float, default=0.97)
    p.add_argument("--f0_min", type=int, default=60)
    p.add_argument("--f0_max", type=int, default=500)
    p.add_argument("--energy_gate_db", type=int, default=25)
    p.add_argument("--med_smooth_frames", type=int, default=3)

    # Outputs
    p.add_argument("--per_frame", action="store_true", help="Save per-frame CSVs and PNG plots")
    p.add_argument("--out", default="cpps_summary.csv")
    p.add_argument("--plots-dir", default="frame_plots", help="Directory for per-file time-course PNGs")

    # Praat-match options (pass-through to compute_cpps_for_file)
    p.add_argument("--praat-match", action="store_true",
                   help="Use Praat-aligned CPPS (power-cepstrum, exp-decay robust trend, Hann 40/20, pre-emph 50 Hz)")
    p.add_argument("--praat-bias-db", type=float, default=None,
                   help="Constant (dB) to add to align Python to Praat (e.g. 6.83).")
    p.add_argument("--hop-ms", type=float, default=20.0,
                   help="Hop size in milliseconds (Praat-match mode). Default: 20 ms.")
    return p

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # expand inputs -> file list
    files = []
    for inp in args.inputs:
        p = Path(inp)
        if p.is_dir():
            files += [str(f) for f in sorted(p.glob("*.wav"))]
        else:
            files.append(str(p))

    # forward flags to compute_cpps_batch
    kwargs = dict(
        frame_ms=args.frame_ms,
        hop_pct=args.hop_pct,
        preemph_alpha=args.preemph_alpha,
        f0_min=args.f0_min,
        f0_max=args.f0_max,
        energy_gate_db=args.energy_gate_db,
        med_smooth_frames=args.med_smooth_frames,
        return_per_frame=args.per_frame,
        praat_match=args.praat_match,
        praat_bias_db=args.praat_bias_db,
        hop_ms=args.hop_ms,
        preemph_from_hz=50.0,
    )

    df, per_frame = compute_cpps_batch(files, **kwargs)
    df.to_csv(args.out, index=False)

    if args.per_frame:
        os.makedirs(args.plots_dir, exist_ok=True)
        for path, pf in per_frame.items():
            stem = Path(path).stem
            # per-frame CSV next to audio stem
            pf.to_csv(f"{stem}_cpps_framewise.csv", index=False)
            # time-course PNG
            times = pf["time_s"].to_numpy() if "time_s" in pf.columns else pf.index.to_numpy().astype(float)
            save_path = Path(args.plots_dir) / f"{stem}_cpps.png"
            save_timecourse_plot(times, pf["cpps_db"].to_numpy(), str(save_path), title=f"CPPS: {stem}")

    print(f"Wrote {args.out} with {len(df)} files.")

if __name__ == "__main__":
    main()
