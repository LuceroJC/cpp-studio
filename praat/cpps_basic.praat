# CPP (basic) estimator per sound selection — for offline clinics
# Usage: open a WAV in Praat, select Sound, then run this script.
# Outputs: mean CPP (dB) to Info window. Simplified; for research/teaching, not diagnosis.


form CPP_basic
real f0min 60
real f0max 500
real preemph 0.97
real frame_ms 40
real hop_pct 50
endform


select Sound all
sound$ = selected$ ("Sound")
fs = Get sampling frequency


# Preemphasis
Filter (pre-emphasis)... 'preemph'


# Frame params
N = round (fs * frame_ms/1000)
H = round (N * hop_pct/100)


# Iterate frames
nframes = floor ((Get number of samples - N) / H) + 1
sum = 0
count = 0
for i to nframes
start = (i-1) * H / fs
end = start + N / fs
Extract part... start end rectangular 1 yes
To Spectrum...
To Cepstrum (real)...
# Search quefrency range
qmin = 1/f0max
qmax = 1/f0min
# Smooth baseline via linear fit in [qmin,qmax] (approx w/ polynomial 1)
Fit polynomial... 1
select Cepstrum cepstrum
peak = Get maximum... qmin qmax Parabolic
base = Get value in point... peak Hertz Linear
cpp = (Get value in point... peak Hertz Linear) - base
sum = sum + cpp
count = count + 1
select all
Remove
endfor


mean = sum / count
writeInfoLine: "CPP_basic (approx) for ", sound$, ": ", fixed$(mean,3), " dB"