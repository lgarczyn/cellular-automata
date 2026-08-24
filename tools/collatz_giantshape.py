#!/usr/bin/env python3
"""The shape of the giant, in the app's own frame. SCOPE: [real-CA].

Compare images/collatz-hex-allones_240-1.png: that is this exact machine at
K = 40, drawn cell by cell in the hex view. This is the same machine and the
same frame at K = 2^16, drawn as blocks, so it is the same picture with more
cells in it. The certified monster (K = 2^22, 20,229,242 odd steps) is again
the same picture, 64x larger in each direction: the design is scale-free.

Frame = TAPE coordinates, as in the app. A cell keeps its position forever.
Position p holds bit (p - S_r) of n_r, where S_r is the number of halvings
done so far, so:

    p <  S_r          consumed by the LeastEdge   -> green   (the right side eats)
    S_r <= p < S_r+b  the number itself           -> purple textures
    p >= S_r + b      beyond the MSB, void        -> dark    (the left side grows)

MSB is on the LEFT, so the green consumed sea is on the RIGHT and the void is
on the LEFT, exactly as in the hex render.

Colours follow the app: void #0b0b14, 0-digit dark, 1-digit purple, solid ones
light purple (in the hex view the fuse is "1 with carry"), LeastEdge green.
Each pixel is a square block of cells (identical cells/pixel in both axes), so
the geometry is true: no stretching.

The climb has a closed form, verified here rather than asserted:

    n_r = 3^r * 2^(K-r) - 1

so the body is two sectors: digits of 3^r on the left (Sierpinski texture,
density 1/2) and the untouched fuse of ones on the right (density 1). The
boundary between them walks left 1 cell/step; the MSB edge advances 1.585
cells/step; the body opens at 0.585 cells/step for exactly K steps.
"""
import os
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")

K = 1 << 16                 # 1/64 the linear size of the 2^22 giant
OUT_W = 1500

VOID = np.array([0x0b, 0x0b, 0x14]) / 255.0
GREEN = np.array([0x39, 0xd3, 0x53]) / 255.0
BODY = LinearSegmentedColormap.from_list(
    "body", ["#1a1e24", "#4c2f9e", "#7c3aed", "#c9a0ff"])   # 0 -> 1 density


def bits_of(n):
    b = n.bit_length()
    return np.unpackbits(np.frombuffer(n.to_bytes((b + 7) // 8, "little"),
                                       dtype=np.uint8), bitorder="little")[:b]


def main():
    t0 = time.time()
    n = (1 << K) - 1
    S = 0
    hist = []                                   # (S_r, n_r)
    while n != 1:
        hist.append((S, n))
        m = 3 * n + 1
        v = (m & -m).bit_length() - 1
        n = m >> v
        S += v
    hist.append((S, n))
    steps = len(hist) - 1
    peak = max(x.bit_length() for _, x in hist)
    span = max(s + x.bit_length() for s, x in hist)
    print("K = %d, %d odd steps, peak %d bits, tape span %d cells, %.1fs"
          % (K, steps, peak, span, time.time() - t0))
    ok = all(hist[r][1] == 3**r * 2**(K - r) - 1 for r in range(0, K, K // 8))
    print("climb closed form n_r = 3^r*2^(K-r)-1 verified at sampled r:", ok)

    # square blocks: identical cells per pixel on both axes
    OUT_ROWS = max(1, int(round(OUT_W * steps / span)))
    cells_x = span / OUT_W
    print("output %d x %d px, block %.0f x %.0f cells (square)"
          % (OUT_W, OUT_ROWS, cells_x, steps / OUT_ROWS))

    img = np.zeros((OUT_ROWS, OUT_W, 3))
    img[:] = VOID
    rows = np.linspace(0, steps, OUT_ROWS).astype(int)

    def col_of(p):                               # MSB (high p) on the LEFT
        return ((span - 1 - p) * OUT_W) // span

    for out_r, r in enumerate(rows):
        S_r, n_r = hist[r]
        raw = bits_of(n_r)
        b = len(raw)
        # consumed sea on the right
        if S_r > 0:
            img[out_r, col_of(S_r - 1):] = GREEN
        # the number, coloured by density of 1-digits per block
        col = col_of(S_r + np.arange(b))
        tot = np.bincount(col, weights=raw, minlength=OUT_W)
        cnt = np.bincount(col, minlength=OUT_W)
        hit = cnt > 0
        img[out_r, hit] = BODY(tot[hit] / cnt[hit])[:, :3]

    fig = plt.figure(figsize=(14, 14 * OUT_ROWS / OUT_W + 3.2), dpi=150)
    ax = fig.add_axes([0.05, 0.30, 0.92, 0.60])
    ax.imshow(img, interpolation="nearest", aspect="auto")
    # anchor every label on a computed cell, not a guessed fraction of the frame
    peak_row = int(K / steps * (OUT_ROWS - 1))
    mid = int(peak_row * 0.55)                       # a row in mid-climb
    S_m, n_m = hist[rows[mid]]
    b_m = n_m.bit_length()
    ax.annotate("the fuse: solid ones the machine has\nnot reached yet "
                "(light, as in the hex view)",
                xy=(col_of((S_m + K) // 2), mid),
                xytext=(OUT_W * 0.30, peak_row * 0.22),
                color="#c9a0ff", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#c9a0ff"))
    ax.annotate("digits of 3^r: Sierpinski texture, density 1/2",
                xy=(col_of((K + S_m + b_m) // 2), mid),
                xytext=(OUT_W * 0.17, peak_row * 0.45),
                color="#8b5cf6", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#8b5cf6"))
    ax.annotate("beyond the MSB: void.\nThe left side grows into it at 1.585 cells/step",
                xy=(col_of(min(span - 1, S_m + b_m + 40000)), mid),
                xytext=(OUT_W * 0.06, peak_row * 0.85),
                color="#9aa4b2", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#9aa4b2"))
    grow = int(OUT_ROWS * 0.62)
    ax.annotate("consumed tape: the right side eats, one cell per halving",
                xy=(col_of(hist[rows[grow]][0] // 2), grow),
                xytext=(OUT_W * 0.50, OUT_ROWS * 0.78),
                color="#06381a", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#0a6b28"))
    ax.annotate("fuse spent at step K: summit, then the generic fall",
                xy=(col_of(K), peak_row), xytext=(OUT_W * 0.36, peak_row * 1.35),
                color="#b8860b", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#b8860b"))
    ax.set_xlabel("tape position: MSB LEFT, LeastEdge eats on the RIGHT "
                  "(same frame as the app's hex view)")
    ax.set_ylabel("odd step")
    ax.set_yticks(np.linspace(0, OUT_ROWS - 1, 6))
    ax.set_yticklabels(["{:,}".format(int(v)) for v in np.linspace(0, steps, 6)])
    ax.set_xticks([])
    fig.suptitle("[real-CA] the shape of the giant. All-ones seed of %s bits, "
                 "%s odd steps, whole life.\nSame machine and same frame as "
                 "images/collatz-hex-allones_240-1.png, which is K = 40 drawn "
                 "cell by cell.\nHere each pixel is a square block of ~%d cells "
                 "a side. The certified monster (K = 2^22, 20,229,242 steps) is "
                 "this picture again, 64x larger."
                 % ("{:,}".format(K), "{:,}".format(steps), cells_x), fontsize=11)

    # inset: real cells at the 3^r / fuse boundary, mid-climb, no downsampling
    r0 = K // 2
    IH, IW = 100, 240
    tile = np.zeros((IH, IW), np.uint8)
    for k in range(IH):
        raw = bits_of(hist[r0 + k][1])
        edge = K - (r0 + k)                     # bits below this are the fuse
        seg = raw[edge - IW // 2: edge + IW // 2]
        tile[k, :] = seg[::-1]                  # MSB left
    axi = fig.add_axes([0.05, 0.045, 0.40, 0.19])
    axi.imshow(tile, cmap=BODY, vmin=0, vmax=1, interpolation="nearest", aspect="auto")
    axi.axvline(IW / 2 - 0.5, color="#39d353", lw=1.0, ls=":")
    axi.set_xticks([]); axi.set_yticks([])
    for s in axi.spines.values():
        s.set_color("#c9a0ff")
    fig.text(0.05, 0.253,
             "real cells at the 3^r / fuse boundary, mid-climb (%d x %d cells, no "
             "downsampling).\nSierpinski texture on the left, solid fuse on the "
             "right, boundary walking left 1 cell per step." % (IH, IW),
             fontsize=8.5, color="#5b3fa8", va="bottom")

    axt = fig.add_axes([0.52, 0.045, 0.45, 0.20])
    axt.axis("off")
    axt.text(0, 1.0,
             "How to read it, in the app's frame:\n"
             "  green   consumed tape (right side eats, 1 cell/halving)\n"
             "  light   the fuse: solid ones, not yet reached\n"
             "  purple  digits of 3^r, density 1/2\n"
             "  dark    void beyond the MSB (left side grows into it)\n\n"
             "The climb is exact, not statistical:\n"
             "    n_r = 3^r * 2^(K-r) - 1   (verified)\n"
             "  fuse shrinks 1 cell/step, MSB edge +1.585 cells/step,\n"
             "  body opens 0.585 cells/step, for exactly K steps,\n"
             "  summit %s bits = K*log2(3), then the generic fall.\n\n"
             "K = 2^22 giant: 20,229,242 odd steps, peak 6,647,814 bits\n"
             "(predicted 6,647,815). Same picture, 64x larger."
             % "{:,}".format(peak),
             fontsize=9.5, va="top", family="monospace")

    out = os.path.join(IMG, "collatz-giant-shape.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote images/collatz-giant-shape.png")


if __name__ == "__main__":
    main()
