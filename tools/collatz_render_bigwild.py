#!/usr/bin/env python3
"""Portraits of the big-tape scan champions (1024/4096/16384-bit seeds).
SCOPE: [real-CA]. Two views per specimen:
  left: whole-life density map (square blocks, tape frame, app colors -
        same convention as collatz-giant-shape.png)
  right: the flash close-up, real cells (front-aligned bit matrix)
"""
import glob
import os
import sys
from math import log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collatz_verifybig import channels, rowscore64

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
SCAN = "/var/tmp/collatz-scratch/leftscan"

VOID = np.array([0x0b, 0x0b, 0x14]) / 255.0
GREEN = np.array([0x39, 0xd3, 0x53]) / 255.0
BODY = LinearSegmentedColormap.from_list(
    "body", ["#1a1e24", "#4c2f9e", "#7c3aed", "#c9a0ff"])


def bits_of_int(n):
    b = n.bit_length()
    return np.unpackbits(np.frombuffer(n.to_bytes((b + 7) // 8, "little"),
                                       dtype=np.uint8),
                         bitorder="little")[:b]


def density_map(n, T, out_w=520):
    """Tape-frame whole-run density map (like the giant-shape figure)."""
    b0 = n.bit_length()
    hist = []
    x, S = n, 0
    for _ in range(T):
        if x <= 1:
            break
        m = 3 * x + 1
        v = (m & -m).bit_length() - 1
        x = m >> v
        S += v
        hist.append((S, x))
    span = max(s + x.bit_length() for s, x in hist)
    rows_out = max(1, int(round(out_w * len(hist) / span)))
    img = np.zeros((rows_out, out_w, 3))
    img[:] = VOID
    take = np.linspace(0, len(hist) - 1, rows_out).astype(int)

    def col_of(p):
        return ((span - 1 - p) * out_w) // span
    for oi, r in enumerate(take):
        S, x = hist[r]
        raw = bits_of_int(x)
        if S > 0:
            img[oi, col_of(S - 1):] = GREEN
        col = col_of(S + np.arange(len(raw)))
        tot = np.bincount(col, weights=raw, minlength=out_w)
        cnt = np.bincount(col, minlength=out_w)
        hit = cnt > 0
        img[oi, hit] = BODY(tot[hit] / cnt[hit])[:, :3]
    return img, len(hist), span, b0, col_of


def flash_matrix(n, k, W=96, before=12, after=20):
    x = n
    rows = []
    for r in range(1, k + after + 1):
        m = 3 * x + 1
        x = m >> ((m & -m).bit_length() - 1)
        if r >= k - before:
            b = x.bit_length()
            top = x >> (b - W)
            rows.append([(top >> (W - 1 - j)) & 1 for j in range(W)])
    return np.array(rows, dtype=np.uint8)


def render_specimen(n, T, tag, title_extra=""):
    f, t, c, best = channels(n, T)
    score, k, w64 = best
    img, steps, span, b0, col_of = density_map(n, T)
    M = flash_matrix(n, k)
    fig = plt.figure(figsize=(14, 6.2), dpi=145)
    ax1 = fig.add_axes([0.05, 0.10, 0.52, 0.74])
    ax1.imshow(img, interpolation="nearest", aspect="auto")
    krow = int(k / steps * (img.shape[0] - 1))
    ax1.axhline(krow, color="#ffd166", lw=1.0, ls=":")
    ax1.text(2, krow - 3, "flash row (step %d)" % k, color="#ffd166",
             fontsize=8.5)
    ax1.set_xlabel("tape (MSB left, LeastEdge green right) - whole life, "
                   "square blocks")
    ax1.set_ylabel("odd step")
    ax1.set_yticks([0, img.shape[0] - 1])
    ax1.set_yticklabels(["0", "{:,}".format(steps)])
    ax1.set_xticks([])
    ax2 = fig.add_axes([0.62, 0.10, 0.35, 0.74])
    ax2.imshow(M, cmap="Purples_r", vmin=0, vmax=1, interpolation="nearest",
               aspect="auto")
    ax2.axhline(12, color="#ff2d6f", lw=1.2)
    ax2.set_xlabel("leading 96 bits (MSB left)")
    ax2.set_yticks([0, 12, len(M) - 1])
    ax2.set_yticklabels(["step %d" % (k - 12), "step %d  FLASH" % k,
                         "step %d" % (k + 20)], fontsize=8)
    fig.suptitle("[real-CA] %s: a %s-bit seed, %s odd steps. Natural flash "
                 "at step %d, front score %.1f bits of evidence.%s\n"
                 "Left: whole life (density map). Right: real leading bits "
                 "around the flash." %
                 (tag, "{:,}".format(n.bit_length()), "{:,}".format(steps),
                  k, f, title_extra), fontsize=11)
    out = os.path.join(IMG, "collatz-bigwild-%s.png" % tag)
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)
    return out


def main():
    for tag, T in (("b1k", 900), ("b4k", 1800), ("b16k", 3600)):
        hits = []
        for path in glob.glob(os.path.join(SCAN, "big_%s_*.txt" % tag)):
            for line in open(path):
                p = line.split()
                hits.append((int(p[0], 16),) + tuple(map(float, p[1:])))
        if not hits:
            print(tag, "no hits")
            continue
        hits.sort(key=lambda h: -max(h[1], h[2], h[3]))
        n = hits[0][0]
        render_specimen(n, T, tag)


if __name__ == "__main__":
    main()
