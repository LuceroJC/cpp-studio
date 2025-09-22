# app/streamlit_app.py
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from cli.cpps import compute_cpps_batch, save_timecourse_plot

st.set_page_config(page_title="CPP Studio", layout="wide")
st.title("CPP Studio — Streamlit")
st.caption("Batch CPPS/CPP with optional Praat-match mode. Not a medical device.")

# ---------------- Sidebar controls ----------------
uploaded = st.file_uploader(
    "Upload WAV files (mono, 16–48 kHz)",
    type=["wav"],
    accept_multiple_files=True,
)
praat_match = st.sidebar.checkbox(
    "Praat-match (Hann 40/20, pre-emph 50 Hz, robust trend)", value=True
)
praat_bias = st.sidebar.number_input(
    "Praat bias (dB)", value=0.0, step=0.25,
    help="Apply a constant dB offset to CPPS (align numerically to Praat if needed)."
)
per_frame = st.sidebar.checkbox("Per-frame outputs (CSV + save PNGs to folder)", value=True)
plots_dir = st.sidebar.text_input("Output directory for per-frame PNGs/CSVs", value="frame_plots")
save_frame_csvs = st.sidebar.checkbox("Also save per-file framewise CSVs to plots_dir", value=True)
run_btn = st.sidebar.button("Run analysis", type="primary")

# ---------------- Helpers ----------------
def _prep_upload_dir() -> Path:
    """
    Create a session-stable temp directory for uploaded files.
    We keep it across reruns during the session.
    """
    if "upload_dir" not in st.session_state:
        st.session_state["upload_dir"] = tempfile.mkdtemp(prefix="cpps_uploads_")
    return Path(st.session_state["upload_dir"])


def _write_uploads_to_dir(files, out_dir: Path) -> list[str]:
    """
    Save uploaded files to out_dir with unique names.
    Returns list of file paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for i, f in enumerate(files):
        stem = Path(f.name).stem
        safe_stem = "".join(c for c in stem if c.isalnum() or c in ("-", "_"))
        fname = f"{i:03d}_{safe_stem}.wav"
        target = out_dir / fname
        with open(target, "wb") as w:
            w.write(f.read())
        paths.append(str(target))
    return paths


# ---------------- Main action ----------------
if run_btn:
    if not uploaded:
        st.warning("Please upload one or more WAV files.")
        st.stop()

    # Write uploads to a session temp directory (clear previous)
    up_dir = _prep_upload_dir()
    try:
        for p in up_dir.glob("*"):
            p.unlink()
    except Exception:
        pass
    wav_paths = _write_uploads_to_dir(uploaded, up_dir)

    with st.spinner("Computing…"):
        df, per_frame_map = compute_cpps_batch(
            wav_paths,
            frame_ms=40,
            hop_pct=50,
            preemph_alpha=0.97,
            f0_min=60,
            f0_max=500,
            energy_gate_db=25,
            med_smooth_frames=3,
            return_per_frame=per_frame,
            praat_match=praat_match,
            praat_bias_db=(praat_bias if praat_bias != 0.0 else None),
            hop_ms=20.0,
            preemph_from_hz=50.0,
        )

    st.success(f"Processed {len(df)} files.")
    st.dataframe(df, use_container_width=True)

    # Download CSV
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download summary CSV",
        data=csv_bytes,
        file_name="cpps_summary_streamlit.csv",
        mime="text/csv",
    )

    # If per-frame is enabled, save PNGs (and optionally per-file framewise CSVs) for ALL files
    if per_frame and per_frame_map:
        os.makedirs(plots_dir, exist_ok=True)
        for path, pf in per_frame_map.items():
            stem = Path(path).stem
            times = pf["time_s"].to_numpy() if "time_s" in pf.columns else np.arange(len(pf), dtype=float)
            out_png = Path(plots_dir) / f"{stem}_cpps.png"
            save_timecourse_plot(times, pf["cpps_db"].to_numpy(), str(out_png), title=f"CPPS: {stem}")

            if save_frame_csvs:
                out_csv = Path(plots_dir) / f"{stem}_cpps_framewise.csv"
                # Ensure ordering of columns for consistency
                cols = [c for c in ("frame_index", "time_s", "cpps_db", "f0_hz") if c in pf.columns]
                pf.to_csv(out_csv, index=False, columns=cols or None)

        msg = f"Saved PNGs for {len(per_frame_map)} files to **{plots_dir}**."
        if save_frame_csvs:
            msg += " Also saved per-file framewise CSVs."
        st.info(msg)
else:
    st.info("Upload WAV files above and click **Run analysis** in the sidebar.")
