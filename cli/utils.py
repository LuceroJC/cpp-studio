from pathlib import Path
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({"figure.dpi": 140, "savefig.bbox": "tight"})


def plot_time_series(pf: pd.DataFrame, title: str = "CPPS over frames"):
    fig = plt.figure()
    plt.plot(pf["cpps_db"])
    plt.xlabel("Frame")
    plt.ylabel("CPPS (dB)")
    plt.title(title)
    return fig


def plot_histogram(pf: pd.DataFrame, title: str = "CPPS distribution"):
    fig = plt.figure()
    vals = pf["cpps_db"].dropna()
    plt.hist(vals, bins=30)
    plt.xlabel("CPPS (dB)")
    plt.ylabel("Count")
    plt.title(title)
    return fig


def save_plots_bundle(per_frame: dict):
    """Yield (wav_path, [tempfile paths]) for inclusion in a ZIP."""
    tmp_outputs = []
    for wav, pf in per_frame.items():
        figs = [
            (plot_time_series(pf, f"{Path(wav).name} — CPPS over time"), "_timeseries.png"),
            (plot_histogram(pf, f"{Path(wav).name} — CPPS histogram"), "_hist.png"),
        ]
        saved = []
        for fig, suffix in figs:
            out = Path(f"{Path(wav).stem}{suffix}")
            fig.savefig(out)
            plt.close(fig)
            saved.append(out)
        yield wav, saved