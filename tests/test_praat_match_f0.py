import numpy as np
from cli.praat_match import cpps_praat_match

def test_f0_present_in_praat_match():
    fs = 16000
    t = np.arange(int(0.8*fs))/fs
    x = 0.1*np.sin(2*np.pi*150*t)  # 150 Hz tone
    per_cpp, mean_cpp, per_f0, mean_f0 = cpps_praat_match(x, fs)
    assert np.isfinite(mean_f0)
    assert 120 <= mean_f0 <= 180