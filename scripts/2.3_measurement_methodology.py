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

COL_FUNC   = "#eeeeee"
COL_RUST   = "#f1d9c0"
COL_CPP    = "#cfd9e6"
COL_R      = "#d9e3cf"
COL_OUT    = "#f0e7d0"
EDGE       = "#3a3a3a"
TEXT       = "#1a1a1a"

def box(ax, x, y, w, h, text, fc, *, fs=9.5, bold=False, italic=False, ha="center"):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=0.7, edgecolor=EDGE, facecolor=fc,
    )
    ax.add_patch(patch)
    weight = "bold" if bold else "normal"
    style  = "italic" if italic else "normal"
    tx = x + w/2 if ha == "center" else x + 0.2
    ax.text(tx, y + h/2, text,
            ha=ha, va="center",
            fontsize=fs, color=TEXT,
            fontweight=weight, fontstyle=style)

def arrow(ax, x1, y1, x2, y2, *, lw=0.9, ls="-", connectionstyle="arc3,rad=0"):
    a = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=11,
        linewidth=lw, color=EDGE,
        shrinkA=2, shrinkB=2,
        linestyle=ls,
        connectionstyle=connectionstyle,
    )
    ax.add_patch(a)


COL_W = 6.0
COL_GAP = 0.4
LEFT = 0.6
GRID_W = 3 * COL_W + 2 * COL_GAP
RIGHT = LEFT + GRID_W
CX = LEFT + GRID_W / 2
RUST_X = LEFT
CPP_X  = LEFT + COL_W + COL_GAP
R_X    = LEFT + 2 * (COL_W + COL_GAP)
COL_CX = [RUST_X + COL_W / 2, CPP_X + COL_W / 2, R_X + COL_W / 2]

TOP_W = 6.4
TOP_H = 1.2
HEADER_H = 0.9
ROW1_H = 1.2
ROW2_H = 1.7
ROW3_H = 1.5
AGG_H = 0.8
GAP_MID = 0.5    # within the three-column block
GAP_OUTER = 0.95  # above headers and below row 3

AGG_Y = 0.6
ROW3_Y = AGG_Y + AGG_H + GAP_OUTER
ROW2_Y = ROW3_Y + ROW3_H + GAP_MID
ROW1_Y = ROW2_Y + ROW2_H + GAP_MID
HEADER_Y = ROW1_Y + ROW1_H + GAP_MID
TOP_Y = HEADER_Y + HEADER_H + GAP_OUTER

MARGIN_X = 0.4
MARGIN_Y = 0.4
X_MIN = LEFT - MARGIN_X
X_MAX = RIGHT + MARGIN_X
Y_MIN = AGG_Y - MARGIN_Y
Y_MAX = TOP_Y + TOP_H + MARGIN_Y
xspan = X_MAX - X_MIN
yspan = Y_MAX - Y_MIN

fig, ax = plt.subplots(figsize=(7.0, 7.0 * yspan / xspan))
ax.set_xlim(X_MIN, X_MAX)
ax.set_ylim(Y_MIN, Y_MAX)
ax.set_aspect("equal")
ax.axis("off")

# top
box(ax, CX - TOP_W / 2, TOP_Y, TOP_W, TOP_H,
    "Callable function",
    COL_FUNC, fs=10, bold=True)

headers = [
    (RUST_X, "Criterion (Rust)",       COL_RUST),
    (CPP_X,  "Google Benchmark (C++)", COL_CPP),
    (R_X,    "bench (R)",              COL_R),
]
for x, label, colour in headers:
    box(ax, x, HEADER_Y, COL_W, HEADER_H, label, colour, bold=True, fs=10.5)

# row 1
box(ax, RUST_X, ROW1_Y, COL_W, ROW1_H,
    "Adaptively-sized samples\n(default 100)",
    COL_RUST, fs=8.8)
box(ax, CPP_X, ROW1_Y, COL_W, ROW1_H,
    "10 repetitions per case",
    COL_CPP, fs=8.8)
box(ax, R_X, ROW1_Y, COL_W, ROW1_H,
    "20 iterations per case",
    COL_R, fs=8.8)

# row 2
box(ax, RUST_X, ROW2_Y, COL_W, ROW2_H,
    "median  +  95 % CI\non the median\n(bootstrap)",
    COL_RUST, fs=8.8)
box(ax, CPP_X, ROW2_Y, COL_W, ROW2_H,
    "median (aggregate row)\n+ 95% t-interval\non the mean of 10 reps",
    COL_CPP, fs=8.8)
box(ax, R_X, ROW2_Y, COL_W, ROW2_H,
    "median (over 20 iters)\n+ minimum-to-median range\n(not a formal CI)",
    COL_R, fs=8.8)

# row 3
box(ax, RUST_X, ROW3_Y, COL_W, ROW3_H,
    "result JSON",
    "#ffffff", fs=8.8, italic=True)
box(ax, CPP_X, ROW3_Y, COL_W, ROW3_H,
    "result JSON",
    "#ffffff", fs=8.8, italic=True)
box(ax, R_X, ROW3_Y, COL_W, ROW3_H,
    "result CSV",
    "#ffffff", fs=8.8, italic=True)

AGG_W = 7.2
box(ax, CX - AGG_W / 2, AGG_Y, AGG_W, AGG_H,
    "Result aggregation",
    "#e8dfe8", fs=10, bold=True)

# arrows (box bottom -> next box top)
arrow(ax, COL_CX[0], ROW3_Y, CX, AGG_Y + AGG_H, connectionstyle="arc3,rad=-0.05")
arrow(ax, COL_CX[1], ROW3_Y, CX, AGG_Y + AGG_H)
arrow(ax, COL_CX[2], ROW3_Y, CX, AGG_Y + AGG_H, connectionstyle="arc3,rad=0.05")

for x in COL_CX:
    arrow(ax, x, HEADER_Y, x, ROW1_Y + ROW1_H)
    arrow(ax, x, ROW1_Y, x, ROW2_Y + ROW2_H)
    arrow(ax, x, ROW2_Y, x, ROW3_Y + ROW3_H)

arrow(ax, CX, TOP_Y, COL_CX[0], HEADER_Y + HEADER_H,
      connectionstyle="arc3,rad=0.05", ls="--")
arrow(ax, CX, TOP_Y, COL_CX[1], HEADER_Y + HEADER_H, ls="--")
arrow(ax, CX, TOP_Y, COL_CX[2], HEADER_Y + HEADER_H,
      connectionstyle="arc3,rad=-0.05", ls="--")

plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig(OUTPUT_DIR / "2.3_measurement_methodology.pdf",
            bbox_inches="tight", pad_inches=0.1)
print("Wrote 2.3_measurement_methodology.pdf")