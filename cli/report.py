# # cli/report.py
# CPP Studio — batch PDF report generator (A4/Letter, margins, optional logo)
# Usage (Windows example):
#   cpps-report --summary cpps_summary.csv --out cpps_batch_report.pdf ^
#       --title "CPP Studio — VOICED Healthy (N=30)" ^
#       --subtitle "Converted from VOICED (WFDB → WAV); 16 kHz mono" ^
#       --paper a4 --margins "0.6" --logo "C:\path\to\logo.png" --logo_width 1.2

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os
from PIL import Image

# --------- Visual defaults (clean, print-friendly) ------------------------------
plt.rcParams.update({
    "figure.dpi": 160,
    "savefig.bbox": None,        # keep full canvas (no tight-crop)
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "font.size": 10,
})

HEADER_DEFAULT = "CPP Studio — Batch Report"
FOOTER_TEXT = (
    "Measurement/visualization software for research/education; not a medical device. "
    "For sensitive audio, prefer the offline CLI."
)

# --------- Utilities ------------------------------------------------------------

def _parse_margins(margin_str: str | None, paper_size: tuple[float, float]) -> dict:
    """
    Convert inches -> figure fraction for left, right, top, bottom margins.
    Accepts:
      - None -> defaults used
      - "0.6" -> all sides 0.6 inch
      - "0.6,0.6,0.7,0.6" -> L,R,T,B inches
    Returns dict with keys left, right, top, bottom in 0..1 fractions.
    """
    W, H = paper_size
    if not margin_str:
        # Reasonable defaults for print (inches)
        L = R = 0.6
        T = 0.7
        B = 0.6
    else:
        parts = [p.strip() for p in margin_str.split(",") if p.strip() != ""]
        if len(parts) == 1:
            v = float(parts[0])
            L = R = T = B = v
        elif len(parts) == 4:
            L, R, T, B = map(float, parts)
        else:
            raise ValueError("Invalid --margins format. Use a single value or 'L,R,T,B' in inches.")
    # Convert inches to figure fraction
    left   = max(0.0, min(1.0, L / W))
    right  = max(0.0, min(1.0, 1.0 - (R / W)))
    bottom = max(0.0, min(1.0, B / H))
    top    = max(0.0, min(1.0, 1.0 - (T / H)))
    if right <= left or top <= bottom:
        raise ValueError("Margins are too large for the selected paper size.")
    return {"left": left, "right": right, "top": top, "bottom": bottom}

def _format_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["mean_cpps_db", "%voiced_frames", "mean_f0_hz", "duration_s"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def _stats_from_df(df: pd.DataFrame) -> tuple[dict, pd.Series, pd.Series, pd.Series]:
    m = pd.to_numeric(df.get("mean_cpps_db"), errors="coerce")
    v = pd.to_numeric(df.get("%voiced_frames"), errors="coerce")
    f0 = pd.to_numeric(df.get("mean_f0_hz"), errors="coerce")

    def s(fn, x):
        try:
            val = fn(x)
            return float(val) if np.isfinite(val) else np.nan
        except Exception:
            return np.nan

    stats = {
        "N files": int(len(df)),
        "CPPS mean": s(np.nanmean, m),
        "CPPS median": s(np.nanmedian, m),
        "CPPS min": s(np.nanmin, m),
        "CPPS max": s(np.nanmax, m),
        "Voiced% mean": s(np.nanmean, v),
        "F0 mean (Hz)": s(np.nanmean, f0),
    }
    return stats, m, v, f0

def _draw_header(ax, title: str, subtitle: str,
                 logo_path: str | None, logo_width_in: float | None,
                 fig, logo_dpi: int = 300):
    ax.axis("off")
    ax.text(0.01, 0.90, title, fontsize=16, weight="bold", va="top", transform=ax.transAxes)
    if subtitle:
        ax.text(0.01, 0.74, subtitle, fontsize=10, color="#444444", va="top", transform=ax.transAxes)

    if not logo_path:
        return

    try:
        # Resolve Windows-friendly absolute path
        lp = os.path.abspath(os.path.expanduser(os.path.expandvars(str(logo_path))))
        if not os.path.isfile(lp):
            ax.text(0.99, 0.98, "[logo path not found]", fontsize=7, color="#999999",
                    ha="right", va="top", transform=ax.transAxes)
            return

        # Open with Pillow (handles PNG/JPG nicely)
        img = Image.open(lp).convert("RGBA")

        # Desired on-page size
        fig_w_in, _ = fig.get_size_inches()
        lw_in = float(logo_width_in or 1.2)
        target_px_w = max(1, int(round(lw_in * logo_dpi)))

        # If source is wider than needed, downscale (best quality); if smaller, upscale once
        if img.width != target_px_w:
            new_h = int(round(img.height * (target_px_w / img.width)))
            img = img.resize((target_px_w, new_h), Image.LANCZOS)

        # Place inside the margins (top-right)
        left, right = fig.subplotpars.left, fig.subplotpars.right
        top, _ = fig.subplotpars.top, fig.subplotpars.bottom
        w_frac = lw_in / fig_w_in
        h_frac = w_frac * (img.height / img.width)
        h_frac = min(h_frac, 0.22)  # cap header height
        pad = 0.006
        x0 = right - w_frac - pad
        y0 = top - h_frac - pad

        ax_logo = fig.add_axes([x0, y0, w_frac, h_frac])
        ax_logo.imshow(img, interpolation="nearest")  # avoid extra blur
        ax_logo.axis("off")

    except Exception as e:
        ax.text(0.99, 0.98, f"[logo error: {e}]", fontsize=7, color="#999999",
                ha="right", va="top", transform=ax.transAxes)

def _draw_stats_text(ax, stats: dict):
    ax.axis("off")
    lines = [
        f"Files: {stats['N files']}",
        (f"CPPS mean/median: {stats['CPPS mean']:.2f} / {stats['CPPS median']:.2f} dB"
         if not np.isnan(stats['CPPS mean']) else "CPPS mean/median: n/a"),
        (f"CPPS min/max: {stats['CPPS min']:.2f} / {stats['CPPS max']:.2f} dB"
         if not np.isnan(stats['CPPS min']) else "CPPS min/max: n/a"),
        (f"Voiced frames (mean): {stats['Voiced% mean']:.1f}%"
         if not np.isnan(stats['Voiced% mean']) else "Voiced frames (mean): n/a"),
        (f"F0 (mean): {stats['F0 mean (Hz)']:.1f} Hz"
         if not np.isnan(stats['F0 mean (Hz)']) else "F0 (mean): n/a"),
    ]
    ax.text(0.01, 0.95, "\n".join(lines), fontsize=10, va="top")

def _hist(ax, m: pd.Series):
    m = pd.to_numeric(m, errors="coerce").dropna()
    if len(m):
        ax.hist(m, bins=20)
    ax.set_title("Mean CPPS (dB) — distribution")
    ax.set_xlabel("CPPS (dB)")
    ax.set_ylabel("Count")

def _scatter(ax, f0: pd.Series, m: pd.Series):
    df_sc = pd.DataFrame({"f0": f0, "m": m}).apply(pd.to_numeric, errors="coerce").dropna()
    if len(df_sc):
        ax.scatter(df_sc["f0"], df_sc["m"], alpha=0.6)
    ax.set_title("Mean F0 vs Mean CPPS")
    ax.set_xlabel("Mean F0 (Hz)")
    ax.set_ylabel("Mean CPPS (dB)")

def _table(ax, df: pd.DataFrame, max_rows=12):
    ax.axis("off")
    cols = ["file", "mean_cpps_db", "%voiced_frames", "mean_f0_hz", "duration_s"]
    df2 = df[cols].copy()
    df2 = _format_numeric_cols(df2)

    half = max_rows // 2
    top = df2.nlargest(half, "mean_cpps_db", keep="all")
    bottom = df2.nsmallest(max_rows - len(top), "mean_cpps_db", keep="all")
    show = pd.concat([top, bottom], ignore_index=True)

    # Format numbers
    fmt = {
        "mean_cpps_db": lambda x: f"{x:.2f}" if pd.notna(x) else "",
        "%voiced_frames": lambda x: f"{x:.1f}" if pd.notna(x) else "",
        "mean_f0_hz": lambda x: f"{x:.1f}" if pd.notna(x) else "",
        "duration_s": lambda x: f"{x:.2f}" if pd.notna(x) else "",
    }
    for c, fn in fmt.items():
        show[c] = show[c].map(fn)

    table = ax.table(cellText=show.values, colLabels=show.columns, loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.1)

    # Header style + zebra stripes
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#f0f0f0")
        elif row % 2 == 0:
            cell.set_facecolor("#fafafa")

# --------- Main report function --------------------------------------------------

def make_report(
    summary_csv: Path,
    out_pdf: Path,
    title: str = HEADER_DEFAULT,
    subtitle: str = "",
    paper: str = "a4",
    margins: str | None = None,
    logo: str | None = None,
    logo_width: float | None = None,
):
    # Paper size (inches)
    if paper.lower() == "letter":
        figsize = (8.5, 11.0)
    else:
        figsize = (8.27, 11.69)  # A4 portrait

    # Load data
    df = pd.read_csv(summary_csv)
    df = _format_numeric_cols(df)
    stats, m, v, f0 = _stats_from_df(df)

    # Figure + margins
    fig = plt.figure(figsize=figsize)
    # Convert margins in inches to fractions
    mfrac = _parse_margins(margins, figsize)
    fig.subplots_adjust(left=mfrac["left"], right=mfrac["right"],
                        top=mfrac["top"], bottom=mfrac["bottom"])

    # Grid inside margins
    gs = GridSpec(5, 2, figure=fig,
                  height_ratios=[0.01, 0.1, 0.30, 0.50, 0.01],
                  hspace=0.45, wspace=0.3)

    # Header band (title/subtitle + optional logo)
    ax_head = fig.add_subplot(gs[0, :])
    _draw_header(ax_head, title, subtitle, logo, logo_width, fig)

    # Stats block (left) + Histogram (right)
    ax_stats = fig.add_subplot(gs[1, :])
    _draw_stats_text(ax_stats, stats)

    ax_hist = fig.add_subplot(gs[2, 0])
    _hist(ax_hist, m)

    # Scatter (right)
    ax_scatter = fig.add_subplot(gs[2, 1])
    _scatter(ax_scatter, f0, m)

    # Table full width
    ax_tbl = fig.add_subplot(gs[3, :])
    _table(ax_tbl, df, max_rows=12)

    # Footer
    ax_foot = fig.add_subplot(gs[4, :])
    ax_foot.axis("off")
    ax_foot.text(0.0, 0.5, FOOTER_TEXT, fontsize=8, color="#666666", va="center")

    # Save
    fig.savefig(out_pdf, format="pdf", bbox_inches=None)
    plt.close(fig)

# --------- Public API (console entry hooks) -------------------------------------

def generate_report(
    summary_csv: str,
    out_pdf: str,
    paper: str = "a4",
    margins_in: float | str | None = None,
    title: str = HEADER_DEFAULT,
    logo_path: str | None = None,
    subtitle: str = "",
    logo_width: float | None = None,
) -> None:
    """
    Thin wrapper to match a friendly signature for console entry points.
    """
    make_report(
        summary_csv=Path(summary_csv),
        out_pdf=Path(out_pdf),
        title=title,
        subtitle=subtitle,
        paper=paper,
        margins=str(margins_in) if isinstance(margins_in, (int, float)) else margins_in,
        logo=logo_path,
        logo_width=logo_width,
    )

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CPP Studio — generate one-page PDF report from summary CSV")
    p.add_argument("--summary", required=True, help="Path to cpps_summary.csv")
    p.add_argument("--out", default="cpps_batch_report.pdf", help="Output PDF path")
    p.add_argument("--title", default=HEADER_DEFAULT, help="Report title")
    p.add_argument("--subtitle", default="", help="Optional subtitle (e.g., dataset slice)")
    p.add_argument("--paper", choices=["a4", "letter"], default="a4", help="Paper size for PDF canvas")
    p.add_argument("--margins",
                   help="Margins in inches. Single value '0.6' or 'L,R,T,B' like '0.6,0.6,0.7,0.6'")
    p.add_argument("--logo", help="Path to a logo image (PNG/JPG/SVG readable by matplotlib)")
    p.add_argument("--logo_width", type=float, help="Logo width in inches (default 1.2)")
    return p

def main() -> None:
    args = build_parser().parse_args()
    # Ensure output dir exists
    out_pdf = Path(args.out)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    # Call through the wrapper for consistency
    generate_report(
        summary_csv=str(Path(args.summary)),
        out_pdf=str(out_pdf),
        paper=args.paper,
        margins_in=args.margins,
        title=args.title,
        logo_path=args.logo,
        subtitle=args.subtitle,
        logo_width=args.logo_width,
    )
    print(f"Report written to {out_pdf}")

# Still allow `python -m cli.report ...`
if __name__ == "__main__":
    main()
