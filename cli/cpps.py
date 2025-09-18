from pathlib import Path
k = int(med_smooth_frames)
if k % 2 == 0:
k += 1
pad = k//2
c = np.copy(cpps)
c_valid = np.where(np.isfinite(c), c, np.nan)
# simple nan‑median filter
smoothed = []
for i in range(len(c)):
a = max(0, i-pad)
b = min(len(c), i+pad+1)
window = c_valid[a:b]
if np.all(np.isnan(window)):
smoothed.append(np.nan)
else:
smoothed.append(np.nanmedian(window))
cpps = np.array(smoothed)


valid = np.isfinite(cpps)
mean_cpps = float(np.nanmean(cpps)) if np.any(valid) else np.nan
median_cpps = float(np.nanmedian(cpps)) if np.any(valid) else np.nan
voiced_pct = float(100.0 * np.sum(valid) / len(cpps)) if len(cpps) else 0.0
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
pf = pd.DataFrame({
"frame_index": np.arange(len(frames)),
"cpps_db": cpps,
"f0_hz": f0s,
})
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