import io
import zipfile
from pathlib import Path
import streamlit as st
import pandas as pd
from cli.cpps import compute_cpps_batch
from cli.utils import save_plots_bundle

st.set_page_config(page_title="CPP Studio", page_icon="🎙️", layout="wide")
st.title("CPP Studio — Cepstral Peak Prominence (Smoothed)")
st.caption("Measurement & visualization utility — not for diagnosis. Use offline CLI for PHI.")

with st.sidebar:
    st.header("Parameters")
    frame_len_ms = st.slider("Frame length (ms)", 20, 60, 40, step=5)
    hop_pct = st.slider("Frame hop (% of frame)", 10, 90, 50, step=5)
    preemph = st.slider("Pre‑emphasis (alpha)", 0.90, 0.99, 0.97, step=0.01)
    f0_min = st.slider("F0 min (Hz)", 40, 120, 60, step=5)
    f0_max = st.slider("F0 max (Hz)", 200, 800, 500, step=10)
    energy_gate_db = st.slider("Energy gate (dB below file RMS)", 0, 40, 25, step=1)
    smooth_med = st.slider("Median smoothing (frames)", 1, 7, 3, step=2)

uploaded = st.file_uploader("Upload WAV files (mono, 16–48 kHz)", type=["wav"], accept_multiple_files=True)

if st.button("Run CPPS"):
    if not uploaded:
        st.warning("Please upload at least one WAV file.")
        st.stop()

    # Save uploads to temp RAM and run
    files = []
    for f in uploaded:
        tmp_path = Path(st.session_state.get("tmp_dir", ".")) / f.name
        tmp_path.write_bytes(f.read())
        files.append(str(tmp_path))

    df, per_frame = compute_cpps_batch(
        files,
        frame_ms=frame_len_ms,
        hop_pct=hop_pct,
        preemph_alpha=preemph,
        f0_min=f0_min,
        f0_max=f0_max,
        energy_gate_db=energy_gate_db,
        med_smooth_frames=smooth_med,
        return_per_frame=True,
    )

    st.subheader("Summary")
    st.dataframe(df, use_container_width=True)

    # Download summary CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download summary CSV", csv, "cpps_summary.csv", "text/csv")

    # Optional per‑frame zip
    st.subheader("Per‑frame data & plots")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for wav, pdf_png in save_plots_bundle(per_frame):
            for p in pdf_png:
                z.writestr(p.name, p.read_bytes())
        # Per‑frame CSVs
        for wav, df_pf in per_frame.items():
            z.writestr(Path(wav).stem + "_perframe.csv", df_pf.to_csv(index=False))
    st.download_button("Download per‑frame ZIP", buf.getvalue(), "cpps_perframe.zip", "application/zip")

st.markdown("---")
st.markdown("**Privacy note:** Web demo does not retain uploads. For sensitive audio, use the offline CLI zip.")