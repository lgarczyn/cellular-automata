#!/usr/bin/env python3
"""The shape of the giant. SCOPE: [real-CA] (LeastEdge frame of CA.CollatzStep).

The certified monster (all-ones seed of 2^22 bits, 20,229,242 odd steps) is
about 7e13 cells, so it cannot be drawn cell by cell. It does not need to be:
the design is scale-free. An all-ones seed of ANY size runs the same program,
so this renders the identical machine at 1/64 the linear size and states the
scale on the figure.

What the climb is, exactly (verified here, not assumed):

    n_r = 3^r * 2^(K-r) - 1     for every step r of the climb

so the body is two sectors: the binary digits of 3^r on the LEFT (a pseudo-
random texture, density 1/2) and an untouched solid block of ones on the RIGHT
(the fuse). The boundary between them marches left at exactly 1 cell per step
(one halving each step), while the MSB edge advances at log2(3) = 1.585, so
the body opens at 0.585 cells per step. The fuse burns out at step K, and the
generic fall begins.

Frame: rows aligned on the LeastEdge (the machine's own frame), MSB LEFT.
Each pixel of the main panel is a block of many cells coloured by the density
of 1-digits, which is an honest summary: the ones sector reads 1.0, the 3^r
sector mottles around 0.5. The inset shows real cells at the sector boundary,
no downsampling.
"""
import os
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")

K = 1 << 16          # seed bits: 1/64 the linear size of the 2^22 giant
OUT_W, OUT_ROWS = 1400, 950


def bits_of(n, width=None):
    b = n.bit_length()
    raw = np.unpackbits(np.frombuffer(n.to_bytes((b + 7) // 8, "little"),
                                      dtype=np.uint8), bitorder="little")[:b]
    return raw                      # index 0 = LSB


def main():
    t0 = time.time()
    n = (1 << K) - 1
    hist = []
    while n != 1:
        hist.append(n)
        m = 3 * n + 1
        v = (m & -m).bit_length() - 1
        n = m >> v
    hist.append(n)
    steps = len(hist) - 1
    peak = max(x.bit_length() for x in hist)
    print("K = %d bits, %d odd steps, peak %d bits, %.1fs"
          % (K, steps, peak, time.time() - t0))

    # verify the closed form of the climb rather than asserting it in prose
    ok = all(hist[r] == 3**r * 2**(K - r) - 1 for r in range(0, K, K // 8))
    print("climb closed form n_r = 3^r*2^(K-r)-1 holds at sampled r:", ok)
    print("cells here: %.2e   cells in the 2^22 giant: %.2e"
          % (steps * peak / 2, 20229242 * 6647814 / 2))

    rows = np.linspace(0, steps, OUT_ROWS).astype(int)
    dens = np.full((OUT_ROWS, OUT_W), np.nan)
    for out_r, r in enumerate(rows):
        raw = bits_of(hist[r])
        b = len(raw)
        col = ((peak - 1 - np.arange(b)) * OUT_W) // peak   # MSB (high i) left
        tot = np.bincount(col, weights=raw, minlength=OUT_W)
        cnt = np.bincount(col, minlength=OUT_W)
        dens[out_r] = np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)

    fig = plt.figure(figsize=(13, 9.5), dpi=150)
    ax = fig.add_axes([0.055, 0.345, 0.90, 0.52])
    cmap = plt.get_cmap("magma").copy()
    cmap.set_bad("#0b0b14")
    im = ax.imshow(dens, cmap=cmap, vmin=0.0, vmax=1.0, aspect="auto",
                   interpolation="nearest")
    peak_row = int(K / steps * (OUT_ROWS - 1))
    ax.axhline(peak_row, color="#39d353", lw=1.2, ls="--")
    ax.text(OUT_W * 0.50, peak_row - 10,
            "fuse burns out at step K = %s: summit, %s bits" % ("{:,}".format(K),
                                                                "{:,}".format(peak)),
            color="#39d353", fontsize=9, va="bottom", ha="left")
    ax.annotate("solid ones: the fuse,\nuntouched, density 1",
                xy=(OUT_W * 0.90, peak_row * 0.35),
                xytext=(OUT_W * 0.60, peak_row * 0.12),
                color="#ffd166", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#ffd166"))
    ax.annotate("digits of 3^r: pseudo-random, density 1/2",
                xy=(OUT_W * 0.55, peak_row * 0.62),
                xytext=(OUT_W * 0.08, peak_row * 0.80),
                color="#7cc7ff", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#7cc7ff"))
    ax.annotate("generic fall: no design left, the body closes",
                xy=(OUT_W * 0.55, peak_row + (OUT_ROWS - peak_row) * 0.45),
                xytext=(OUT_W * 0.30, peak_row + (OUT_ROWS - peak_row) * 0.80),
                color="#ff9ecb", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#ff9ecb"))
    ax.set_xlabel("cells, MSB LEFT, rows aligned on the LeastEdge (right edge)")
    ax.set_ylabel("odd step")
    ax.set_yticks(np.linspace(0, OUT_ROWS - 1, 6))
    ax.set_yticklabels(["{:,}".format(int(v)) for v in np.linspace(0, steps, 6)])
    ax.set_xticks([])
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.008,
                 label="density of 1-digits per block")
    fig.suptitle("[real-CA] the shape of the giant. All-ones seed of %s bits, "
                 "%s odd steps, whole life,\neach pixel a block of ~%d x %d "
                 "cells. The certified monster (2^22 bits, 20,229,242 steps) is "
                 "this same shape\n64x larger in each direction: the design is "
                 "scale-free, only the labels change."
                 % ("{:,}".format(K), "{:,}".format(steps),
                    peak // OUT_W, max(1, steps // OUT_ROWS)), fontsize=11)

    # inset: real cells straddling the sector boundary, mid-climb, no downsampling
    r0 = K // 2
    IH, IW = 110, 260
    tile = np.zeros((IH, IW), np.uint8)
    for k in range(IH):
        raw = bits_of(hist[r0 + k])
        edge = K - (r0 + k)                 # boundary: bits below it are the fuse
        lo = edge - IW // 2
        seg = raw[lo:lo + IW]
        tile[k, :] = seg[::-1]              # MSB left
    axi = fig.add_axes([0.055, 0.045, 0.42, 0.185])
    axi.imshow(tile, cmap="magma", vmin=0, vmax=1, interpolation="nearest",
               aspect="auto")
    axi.axvline(IW / 2 - 0.5, color="#39d353", lw=1.0, ls=":")
    axi.set_xticks([]); axi.set_yticks([])
    for s in axi.spines.values():
        s.set_color("#ffd166")
    fig.text(0.055, 0.253,
             "real cells at the sector boundary, mid-climb (%d x %d cells, no "
             "downsampling): 3^r digits\non the left, fuse on the right, boundary "
             "walking left 1 cell per step" % (IH, IW),
             fontsize=8.5, color="#b8860b", va="bottom")

    axt = fig.add_axes([0.53, 0.045, 0.42, 0.20])
    axt.axis("off")
    axt.text(0, 1.0,
             "The climb is exact, not statistical:\n"
             "    n_r = 3^r * 2^(K-r) - 1\n"
             "verified at sampled r for K = %s.\n\n"
             "  - fuse (ones) shrinks 1 cell/step\n"
             "  - MSB edge advances log2(3) = 1.585 cells/step\n"
             "  - body opens 0.585 cells/step, for exactly K steps\n"
             "  - summit %s bits = K*log2(3), then generic fall\n\n"
             "2^22 giant: 20,229,242 odd steps, peak 6,647,814 bits,\n"
             "predicted peak 6,647,815. Same picture, 64x."
             % ("{:,}".format(K), "{:,}".format(peak)),
             fontsize=9.5, va="top", family="monospace")

    out = os.path.join(IMG, "collatz-giant-shape.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote images/collatz-giant-shape.png")


if __name__ == "__main__":
    main()
