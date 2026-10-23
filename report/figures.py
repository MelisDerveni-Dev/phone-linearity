"""Report charts drawn from existing result tables; nothing is refitted here.

Run after `python -m calib analyse` and `python -m calib evidence`.
"""
import csv
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
sys.path.insert(0, str(ROOT / "src"))
from calib.data import load_csv  # noqa: E402

G = 9.81
RAW, CAL, INK, MUTED, LINE = "#b1b8b2", "#23665e", "#233431", "#66736e", "#aebcb1"


def rows(path):
    with (ROOT / path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def style(ax):
    ax.grid(axis="y", color="#e1e6e1", linewidth=.6)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(LINE)
    ax.tick_params(labelsize=8, length=0)


def before_after(target):
    poses = rows("results/analysis-2026-10-23/static-test.csv")
    still = rows("results/evidence-2026-10-23/linearity.csv")
    ramps = rows("results/evidence-2026-10-23/ramp-tilt.csv")
    fig, (left, right) = plt.subplots(1, 2, figsize=(6.6, 2.5), gridspec_kw={"width_ratios": [1, 1.55]})
    x = np.arange(len(poses))
    left.bar(x - .19, [float(r["raw_vector_error_m_s2"]) for r in poses], .38, color=RAW, label="Uncalibrated")
    left.bar(x + .19, [float(r["corrected_vector_error_m_s2"]) for r in poses], .38, color=CAL, label="Calibrated")
    left.set_xticks(x, [r["pose"].replace("-", "−").lower() for r in poses])
    left.set_ylabel("Error (m/s²)", fontsize=8)
    left.set_title("(a) Six test poses: distance from true gravity", fontsize=8, color=INK, loc="left")
    left.set_ylim(0, .44)
    left.legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
    style(left)
    # Tilted recordings only (rows after the six test poses), sorted by ramp angle.
    tilted = sorted(zip(ramps, still[6:]), key=lambda pair: float(pair[0]["reference_deg"]))
    labels = [f"{float(r['reference_deg']):.0f}°" for r, _ in tilted]
    raw = [G + float(s["raw_magnitude_error_m_s2"]) for _, s in tilted]
    cal = [G + float(s["full_magnitude_error_m_s2"]) for _, s in tilted]
    pos = np.arange(len(tilted))
    right.axhline(G, color=INK, lw=.9)
    right.text(pos[-1] + .4, G + .004, "9.81 (correct)", fontsize=7, color=INK, va="bottom", ha="right")
    right.vlines(pos, raw, cal, color="#d9e1da", lw=1.2, zorder=1)
    right.scatter(pos, raw, s=18, color=RAW, zorder=2)
    right.scatter(pos, cal, s=18, color=CAL, zorder=3)
    right.set_xticks(pos, labels, fontsize=7)
    right.set_xlabel("Ramp angle", fontsize=8)
    right.set_ylim(9.68, 9.93)
    right.set_ylabel("Reading of the still phone (m/s²)", fontsize=8)
    right.set_title("(b) Tilted phone, recorded on later days", fontsize=8, color=INK, loc="left")
    style(right)
    fig.tight_layout(pad=.4, w_pad=1.6)
    fig.savefig(target / "before-after.png", dpi=220, facecolor="#fffefa")
    plt.close(fig)


def shaking(target):
    limit = load_csv(ROOT / "data/processed/angles-2026-10-22/limit.csv")
    t = limit.t - limit.t[0]
    magnitude = np.linalg.norm(limit.xyz, axis=1)
    bins = np.minimum((t / t[-1] * 500).astype(int), 499)
    lo = [magnitude[bins == k].min() for k in range(500)]
    hi = [magnitude[bins == k].max() for k in range(500)]
    fig, ax = plt.subplots(figsize=(6.6, 1.9))
    ax.fill_between(np.linspace(0, t[-1], 500), lo, hi, color="#bf7055", alpha=.55, lw=0, label="Shaken phone")
    ax.axhline(G, color=CAL, lw=1.4, label="Phone at rest (9.81)")
    ax.set(xlabel="Time (s)", ylim=(0, 125), xlim=(0, t[-1]))
    ax.set_ylabel("Total reading (m/s²)", fontsize=8)
    ax.xaxis.label.set_size(8)
    ax.legend(frameon=False, fontsize=7, loc="upper right", ncol=2)
    style(ax)
    fig.tight_layout(pad=.4)
    fig.savefig(target / "shaking.png", dpi=220, facecolor="#fffefa")
    plt.close(fig)


def main():
    target = BASE / "figures"
    target.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})
    before_after(target)
    shaking(target)


if __name__ == "__main__":
    main()
