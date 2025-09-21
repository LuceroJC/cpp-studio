from pathlib import Path
import os
import numpy as np
import pandas as pd
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import get_window
from scipy.fft import rfft, irfft, rfftfreq
from .praat_match import cpps_praat_match    


# --------- helpers ---------
def save_timecourse_plot(times_s: np.ndarray, cpps_db: np.ndarray, out_png: str, title: str = "CPPS time course"):
    """Save a simple CPPS time-course PNG."""
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.plot(times_s, cpps_db, linewidth=1.2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("CPPS (dB)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def write_frame_csv(path: str, wav_path: str, times_s: np.ndarray, cpps_db: np.ndarray, f0_hz: np.ndarray | None = None):
    """Write per-frame CSV with file, time_s, cpps_db, (optional) f0_hz."""
    data = {
        "file": [os.path.basename(wav_path)] * len(times_s),
        "time_s": times_s,
        "cpps_db": cpps_db,
    }
    if f0_hz is not None:
        data["f0_hz"] = f0_hz
    pd.DataFrame(data).to_csv(path, index=False)
# ---------------------------


# Simple F0 band -> quefrency window (seconds)
def _q_range(f0_min, f0_max):
    return 1.0 / f0_max, 1.0 / f0_min


def _preemphasis(x, alpha=0.97):
    y = np.copy(x)
    y[1:] = x[1:] - alpha * x[:-1]
    return y


def _frame_signal(x, fs, frame_ms=40, hop_pct=50):
    N = int(frame_ms * 1e-3 * fs)
    H = max(1, int(N * (hop_pct / 100)))
    w = get_window("hamming", N, fftbins=True)
    frames = []
    for start in range(0, len(x) - N + 1, H):
        frames.append(x[start : start + N] * w)
    return np.array(frames), N, H


def _energy_db(x):
    rms = np.sqrt(np.mean(x**2) + 1e-12)
    return 20 * np.log10(rms + 1e-12)


def _cpp_single_frame(frame, fs, f0_min=60, f0_max=500):
    # Cepstrum of log magnitude spectrum
    spec = np.abs(rfft(frame)) + 1e-12
    log_mag = np.log(spec)
    cep = irfft(log_mag)
    qmin, qmax = _q_range(f0_min, f0_max)
    # Map quefrency range to samples of cepstrum domain
    # Cepstrum length equals frame length (time samples)
    t = np.arange(len(cep)) / fs
    mask = (t >= qmin) & (t <= qmax)
    if not np.any(mask):
        return np.nan, np.nan

    c_seg = cep[mask]
    t_seg = t[mask]

    # Linear regression baseline through the segment
    A = np.vstack([t_seg, np.ones_like(t_seg)]).T
    m, b = np.linalg.lstsq(A, c_seg, rcond=None)[0]
    baseline = m * t_seg + b

    # Peak prominence (in log-amp units); convert to dB (factor ~8.686)
    peak_val = np.max(c_seg)
    peak_idx = np.argmax(c_seg)
    peak_base = baseline[peak_idx]
    cpp = (peak_val - peak_base) * 8.685889638

    # F0 estimate from peak location
    q_peak = t_seg[peak_idx]
    f0 = 1.0 / q_peak if q_peak > 0 else np.nan
    return cpp, f0


def compute_cpps_for_file(
    path,
    frame_ms=40,
    hop_pct=50,
    preemph_alpha=0.97,
    f0_min=60,
    f0_max=500,
    energy_gate_db=25,
    med_smooth_frames=3,
    return_per_frame=False,
    *,
    # NEW: Praat-aligned options
    praat_match: bool = False,
    praat_bias_db: float | None = None,
    hop_ms: float | None = 20.0,  # used only in Praat-match mode
    preemph_from_hz: float = 50.0,  # used only in Praat-match mode
):
    """
    Compute CPPS summary (and optionally per-frame) for one file.

    Two modes:
      - Default (your original): real-cepstrum baseline via LS line, Hamming, hop_pct, _preemphasis(alpha).
      - Praat-match: power-cepstrum, Hann 40/20, pre-emph from 50 Hz, exp-decay robust trend (via cpps_praat_match).
    """
    x, fs = sf.read(path)
    if x.ndim > 1:
        x = np.mean(x, axis=1)
    x = x.astype(np.float64)

        # ---------- Praat-match path ----------
    if praat_match:
        # Try to get CPP and F0 (new 4-tuple); fall back to old 2-tuple gracefully
        res = cpps_praat_match(
            x,
            fs,
            f0min=float(f0_min),
            f0max=float(f0_max),
            frame_ms=float(frame_ms) if frame_ms else 40.0,
            hop_ms=float(hop_ms) if hop_ms else 20.0,
            preemph_from_hz=float(preemph_from_hz),
            gate_db=float(energy_gate_db) if energy_gate_db is not None else 20.0,
        )
        if isinstance(res, tuple) and len(res) == 4:
            per_frame, mean_cpp, f0_series, mean_f0 = res
        else:
            per_frame, mean_cpp = res  # old signature
            f0_series = np.full_like(per_frame, np.nan, dtype=float)
            mean_f0 = np.nan

        # Optional constant bias to align to Praat numerically (CPP only)
        if praat_bias_db is not None and np.isfinite(mean_cpp):
            mean_cpp = float(mean_cpp) + float(praat_bias_db)
            if per_frame.size:
                per_frame = per_frame + float(praat_bias_db)

        # Per-frame DataFrame with time stamps
        if return_per_frame:
            n = int(len(per_frame))
            hop_s = (float(hop_ms) if hop_ms else 20.0) * 1e-3
            frame_s = (float(frame_ms) if frame_ms else 40.0) * 1e-3
            times = np.arange(n) * hop_s + 0.5 * frame_s
            pf = pd.DataFrame(
                {
                    "frame_index": np.arange(n, dtype=int),
                    "time_s": times,
                    "cpps_db": per_frame if per_frame.size else np.array([], dtype=float),
                    "f0_hz": f0_series if f0_series.size else np.array([], dtype=float),
                }
            )

        # Summary metrics
        if per_frame.size:
            median_cpp = float(np.nanmedian(per_frame))
            voiced_pct = float(100.0 * np.isfinite(per_frame).mean())
            n_frames = int(len(per_frame))
        else:
            median_cpp = np.nan
            voiced_pct = 0.0
            n_frames = 0

        duration = len(x) / fs
        summary = {
            "file": Path(path).name,
            "mean_cpps_db": round(float(mean_cpp), 3) if np.isfinite(mean_cpp) else None,
            "median_cpps_db": round(float(median_cpp), 3) if np.isfinite(median_cpp) else None,
            "%voiced_frames": round(voiced_pct, 2),
            "mean_f0_hz": round(float(mean_f0), 2) if np.isfinite(mean_f0) else None,  # now set
            "frames": n_frames,
            "duration_s": round(duration, 3),
        }
        return (summary, pf) if return_per_frame else summary


    # ---------- Original path (unchanged behavior) ----------
    x = _preemphasis(x, preemph_alpha)

    frames, N, H = _frame_signal(x, fs, frame_ms, hop_pct)
    file_db = _energy_db(x)

    out = []
    for fr in frames:
        if _energy_db(fr) < file_db - energy_gate_db:
            out.append((np.nan, np.nan))
            continue
        cpp, f0 = _cpp_single_frame(fr, fs, f0_min, f0_max)
        out.append((cpp, f0))

    vals = np.array(out)
    cpps = vals[:, 0]
    f0s = vals[:, 1]

    # Median smoothing for CPPS across frames (odd window only)
    if med_smooth_frames and med_smooth_frames > 1:
        k = int(med_smooth_frames)
        if k % 2 == 0:
            k += 1
        pad = k // 2
        c = np.copy(cpps)
        c_valid = np.where(np.isfinite(c), c, np.nan)
        smoothed = []
        for i in range(len(c)):
            a = max(0, i - pad)
            b = min(len(c), i + pad + 1)
            window = c_valid[a:b]
            smoothed.append(np.nan if np.all(np.isnan(window)) else np.nanmedian(window))
        cpps = np.array(smoothed)

    valid = np.isfinite(cpps)
    mean_cpps = float(np.nanmean(cpps)) if np.any(valid) else np.nan
    median_cpps = float(np.nanmedian(cpps)) if np.any(valid) else np.nan
    voiced_pct = float(np.sum(valid) / len(cpps) * 100.0) if len(cpps) else 0.0
    mean_f0 = float(np.nanmean(f0s)) if np.any(np.isfinite(f0s)) else np.nan
    duration = len(x) / fs

    summary = {
        "file": Path(path).name,
        "mean_cpps_db": round(mean_cpps, 3) if np.isfinite(mean_cpps) else None,
        "median_cpps_db": round(median_cpps, 3) if np.isfinite(median_cpps) else None,
        "%voiced_frames": round(voiced_pct, 2),
        "mean_f0_hz": round(mean_f0, 2) if np.isfinite(mean_f0) else None,
        "frames": int(len(frames)),
        "duration_s": round(duration, 3),
    }

    if return_per_frame:
        # center-of-frame time = i*H/fs + N/(2*fs)
        n = len(frames)
        hop_s = H / fs
        frame_s = N / fs
        times = np.arange(n) * hop_s + 0.5 * frame_s
        pf = pd.DataFrame(
            {
                "frame_index": np.arange(n),
                "time_s": times,
                "cpps_db": cpps,
                "f0_hz": f0s,
            }
        )
        return summary, pf
    return summary


def compute_cpps_batch(paths, **kwargs):
    summaries = []
    per_frame = {}
    for p in paths:
        if kwargs.get("return_per_frame", False):
            s, pf = compute_cpps_for_file(p, **kwargs)
            summaries.append(s)
            per_frame[p] = pf
        else:
            summaries.append(compute_cpps_for_file(p, **kwargs))
    df = pd.DataFrame(summaries)
    return df, per_frame
