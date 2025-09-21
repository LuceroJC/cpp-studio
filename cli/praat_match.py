# cpps/praat_match.py
import numpy as np
from numpy.fft import rfft, irfft

def _preemphasis_from_hz(x, fs, f0=50.0):
    # y[n] = x[n] - a*x[n-1], a = exp(-2π f0 / fs) ≈ Praat's "pre-emphasis from"
    a = float(np.exp(-2.0 * np.pi * f0 / fs))
    y = np.empty_like(x)
    y[0] = x[0]
    y[1:] = x[1:] - a * x[:-1]
    return y

def _frame_signal(x, fs, frame_ms=40.0, hop_ms=20.0, window="hann"):
    n = int(round(fs * frame_ms / 1000.0))
    h = int(round(fs * hop_ms / 1000.0))
    if n <= 0 or h <= 0: raise ValueError("bad frame/hop")
    w = np.hanning(n) if window == "hann" else np.ones(n)
    frames = []
    for start in range(0, max(0, len(x) - n + 1), h):
        frames.append(x[start:start+n] * w)
    return np.stack(frames, axis=0), n, h

def _power_cepstrum_db(frame, fft_len=None, eps=1e-12):
    # Power spectrum -> log -> real cepstrum (power cepstrum in dB-like units)
    if fft_len is None:
        fft_len = int(2 ** np.ceil(np.log2(len(frame))))
    X = rfft(frame, n=fft_len)
    logP = np.log(np.maximum((np.abs(X) ** 2), eps))
    c = irfft(logP, n=fft_len)  # real cepstrum
    # scale to dB-like: Praat's PowerCepstrum is already "dB-like";
    # we keep values in natural units and convert differences to dB with 8.6859
    return c

def _huber_weights(r, k=1.345):
    # Huber psi: |r|<=k -> 1, else k/|r|
    a = np.abs(r)
    w = np.ones_like(a)
    mask = a > k
    w[mask] = (k / a[mask])
    return w

def _robust_line_exp_decay(q, y, iters=15):
    # Fit trend ~ a + b*q with Huber IRLS in natural units; return a,b
    # (Exponential decay in linearized (natural-log) corresponds to straight line here.)
    X = np.c_[np.ones_like(q), q]
    a, b = 0.0, 0.0
    w = np.ones_like(q)
    for _ in range(iters):
        W = (w[:, None] * X)
        # Solve weighted least squares
        beta, *_ = np.linalg.lstsq(W, w * y, rcond=None)
        a, b = beta
        r = (y - (a + b * q))
        s = np.median(np.abs(r)) + 1e-12
        w = _huber_weights(r / (1.4826 * s))
    return a, b

def cpps_praat_match(x, fs, f0min=60.0, f0max=500.0,
                     frame_ms=40.0, hop_ms=20.0,
                     preemph_from_hz=50.0, gate_db=20.0):
    """Return (per_frame_cpp_db, mean_cpp_db) aligned to Praat settings."""
    # pre-emphasis
    x = _preemphasis_from_hz(x.astype(np.float64), fs, preemph_from_hz)

    # whole-file RMS for gating
    file_rms = np.sqrt(np.mean(x**2) + 1e-18)
    file_rms_db = 20.0 * np.log10(file_rms + 1e-18)

    frames, n, h = _frame_signal(x, fs, frame_ms, hop_ms, window="hann")
    frame_len_s = n / float(fs)
    qmin = 1.0 / f0max
    qmax = min(1.0 / f0min, 0.99 * frame_len_s)

    # quefrency axis for the cepstrum
    fft_len = int(2 ** np.ceil(np.log2(n)))
    q_axis = np.arange(fft_len) / float(fs)

    # indices in the search window
    i0 = int(np.floor(qmin * fs))
    i1 = int(np.floor(qmax * fs))
    i1 = max(i1, i0 + 2)

    per_frame = []
    for fr in frames:
        fr_rms = np.sqrt(np.mean(fr**2) + 1e-18)
        fr_rms_db = 20.0 * np.log10(fr_rms + 1e-18)
        if fr_rms_db < file_rms_db - gate_db:
            continue

        c = _power_cepstrum_db(fr, fft_len=fft_len)

        # smooth a little in quefrency (~1–2 ms window)
        qwin = max(2, int(round(0.0015 * fs)))
        if qwin > 1:
            ker = np.ones(qwin) / qwin
            c_sm = np.convolve(c, ker, mode="same")
        else:
            c_sm = c

        q = q_axis[i0:i1]
        y = c_sm[i0:i1]  # natural units

        # peak location (parabolic interp around discrete max)
        k = i0 + np.argmax(y)
        if 1 <= k < len(c_sm)-1:
            # parabolic vertex via three-point formula
            y0, y1, y2 = c_sm[k-1], c_sm[k], c_sm[k+1]
            denom = (y0 - 2*y1 + y2) + 1e-12
            delta = 0.5 * (y0 - y2) / denom
        else:
            delta = 0.0
        q_peak = (k + delta) / fs

        # robust straight-line fit ("Exponential decay" trend) over [qmin,qmax]
        a, b = _robust_line_exp_decay(q, y, iters=15)
        # trend at peak
        trend_at_peak = a + b * q_peak

        # prominence: (peak - trend) in natural units -> dB
        peak_val = np.interp(q_peak, q_axis, c_sm)
        cpp_db = (peak_val - trend_at_peak) * 8.685889638  # ln → dB
        per_frame.append(cpp_db)

    if not per_frame:
        return np.array([]), np.nan
    per_frame = np.array(per_frame, dtype=float)
    return per_frame, float(np.mean(per_frame))
