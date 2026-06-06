from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9.5,
    "axes.linewidth": 0.6,
})

COL_RAW    = "#e8eef4"
COL_PREP   = "#dde6ed"
COL_RUST   = "#f1d9c0"
COL_CPP    = "#cfd9e6"
COL_R      = "#d9e3cf"
COL_ORCH   = "#e8dfe8"
COL_OUT    = "#f0e7d0"
EDGE       = "#3a3a3a"
TEXT       = "#1a1a1a"

def box(ax, x, y, w, h, text, fc, *, fs=9.5, bold=False, italic=False):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=0.7, edgecolor=EDGE, facecolor=fc,
    )
    ax.add_patch(patch)
    weight = "bold" if bold else "normal"
    style  = "italic" if italic else "normal"
    ax.text(x + w/2, y + h/2, text,
            ha="center", va="center",
            fontsize=fs, color=TEXT,
            fontweight=weight, fontstyle=style)

def arrow(ax, x1, y1, x2, y2, *, lw=0.9, connectionstyle="arc3,rad=0"):
    a = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=11,
        linewidth=lw, color=EDGE,
        shrinkA=2, shrinkB=2,
        connectionstyle=connectionstyle,
    )
    ax.add_patch(a)

HEADER_Y = 13.4
HEADER_GAP = 0.35
CONTENT_TOP = 10.6
CONTENT_OFFSET = (HEADER_Y - 0.5 - HEADER_GAP) - CONTENT_TOP

fig, ax = plt.subplots(figsize=(10, 4.6))
ax.set_xlim(0, 23)
ax.set_ylim(4.85, HEADER_Y + 0.2)
ax.set_aspect("equal")
ax.axis("off")

X_RAW   = 0.3
X_PREP  = 4.8
X_LANG  = 9.6
X_ORCH  = 15.0
X_OUT   = 19.4
BOX_W   = 3.4

headers = [
    (X_RAW  + BOX_W/2, HEADER_Y, "Raw data"),
    (X_PREP + BOX_W/2, HEADER_Y, "Preparation"),
    (X_LANG + BOX_W/2, HEADER_Y, "Benchmarking"),
    (X_ORCH + BOX_W/2, HEADER_Y, "Orchestration"),
    (X_OUT  + BOX_W/2, HEADER_Y, "Results"),
]
for x, y, txt in headers:
    ax.text(x, y, txt, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=TEXT,
            style="italic")
    ax.plot([x-1.7, x+1.7], [y-0.34, y-0.34],
            color=EDGE, lw=0.5)

# 1: raw data
RAW1_Y = 9.2 + CONTENT_OFFSET
RAW2_Y = 4.6 + CONTENT_OFFSET
box(ax, X_RAW, RAW1_Y, BOX_W, 1.2,
    "E. coli K-12 MG1655\nNCBI NC_000913.3", COL_RAW)
box(ax, X_RAW, RAW2_Y, BOX_W, 1.2,
    "Open Tree of Life\nv16.1 grafted solution", COL_RAW)

# 2: prep
PREP_SCRIPT_Y = 9.2 + CONTENT_OFFSET
box(ax, X_PREP, PREP_SCRIPT_Y, BOX_W, 1.2,
    "prepare_data.py",
    COL_PREP, fs=8.8)

PREP_FILES_Y = 3.6 + CONTENT_OFFSET
box(ax, X_PREP, PREP_FILES_Y, BOX_W, 3.0,
    "Prepared files\n\n"
    "kmp_text.txt\n"
    "kmp_pattern.txt\n"
    "seq_pair_a.txt\n"
    "seq_pair_b.txt\n"
    "tree_[...].nwk",
    COL_PREP, fs=8.4)

# 3: benchmarking
LANG_H = 1
RUST_Y = 9.6 + CONTENT_OFFSET
CPP_Y  = 6.4 + CONTENT_OFFSET
R_Y    = 3.2 + CONTENT_OFFSET

box(ax, X_LANG, RUST_Y, BOX_W, LANG_H,
    "Criterion (Rust)",
    COL_RUST, fs=8.4)

box(ax, X_LANG, CPP_Y, BOX_W, LANG_H,
    "Google Benchmark\n"
    "(C++)",
    COL_CPP, fs=8.4)

box(ax, X_LANG, R_Y, BOX_W, LANG_H,
    "bench (R)",
    COL_R, fs=8.4)

# 4: orchestrator
ORCH_Y = 6.4 + CONTENT_OFFSET
box(ax, X_ORCH, ORCH_Y, BOX_W, LANG_H,
    "Python orchestrator",
    COL_ORCH, fs=8.4)

# 5: results
OUT1_Y = 8.8 + CONTENT_OFFSET
OUT2_Y = 7.2 + CONTENT_OFFSET
box(ax, X_OUT, OUT1_Y, BOX_W, 1.0,
    "results.csv", COL_OUT, bold=True, fs=10.5)
box(ax, X_OUT, OUT2_Y, BOX_W, 1.0,
    "results.parquet", COL_OUT, bold=True, fs=10.5)

# arrows 
arrow(ax, X_RAW + BOX_W, RAW1_Y + 0.6,  X_PREP, PREP_SCRIPT_Y + 0.8)
arrow(ax, X_RAW + BOX_W, RAW2_Y + 0.6,  X_PREP, PREP_SCRIPT_Y + 0.4)

arrow(ax, X_PREP + BOX_W/2, PREP_SCRIPT_Y,
      X_PREP + BOX_W/2, PREP_FILES_Y + 3.0, lw=1.0)

prep_right_x = X_PREP + BOX_W
prep_centre_y = PREP_FILES_Y + 1.5
arrow(ax, prep_right_x, prep_centre_y + 0.6,
      X_LANG, RUST_Y + LANG_H/2,
      connectionstyle="arc3,rad=-0.10")
arrow(ax, prep_right_x, prep_centre_y,
      X_LANG, CPP_Y + LANG_H/2)
arrow(ax, prep_right_x, prep_centre_y - 0.6,
      X_LANG, R_Y + LANG_H/2,
      connectionstyle="arc3,rad=0.10")

arrow(ax, X_LANG + BOX_W, RUST_Y + LANG_H/2,
      X_ORCH, ORCH_Y + LANG_H/2 + 0.4,
      connectionstyle="arc3,rad=0.12")
arrow(ax, X_LANG + BOX_W, CPP_Y + LANG_H/2,
      X_ORCH, ORCH_Y + LANG_H/2)
arrow(ax, X_LANG + BOX_W, R_Y + LANG_H/2,
      X_ORCH, ORCH_Y + LANG_H/2 - 0.4,
      connectionstyle="arc3,rad=-0.12")

arrow(ax, X_ORCH + BOX_W, ORCH_Y + LANG_H/2 + 0.2,
      X_OUT, OUT1_Y + 0.5, connectionstyle="arc3,rad=-0.10")
arrow(ax, X_ORCH + BOX_W, ORCH_Y + LANG_H/2 - 0.2,
      X_OUT, OUT2_Y + 0.5, connectionstyle="arc3,rad=0.10")

plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig(OUTPUT_DIR / "2.1_pipeline_overview.pdf",
            bbox_inches="tight", pad_inches=0.05)
print("Wrote 2.1_pipeline_overview.pdf")