#!/usr/bin/env python3
"""Bulk physics on kilobit tapes. SCOPE: [real-CA].
Big tapes are interesting not for their tail statistics but because they
give ROOM: designed objects can live hundreds of cells from both edges.

  collatz-bulk-lightcone.png  flip ONE mid-tape bit, XOR the two real runs:
                              the influence wedge climbs at exactly log2(3),
                              parallel to the front (you cannot shoot the
                              left edge from inside); when the sea reads the
                              flipped bit, the entire future rewrites.
  collatz-bulk-gliders.png    x3 traveling crystals (rigid shift iff
                              3 = 2^k mod d) alive mid-tape in the real CA:
                              d=13 stripes at 4 cells/step over d=5 stripes
                              at 3 cells/step, envelopes at 1.585, and the
                              mixing wedge where they meet.
"""
import os
import random
import sys
from math import log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
LOG23 = log2(3)


def run_tapes(n, T):
    """List of (S, x) per row, real dynamics."""
    out = []
    x, S = n, 0
    for _ in range(T):
        if x <= 1:
            break
        m = 3 * x + 1
        v = (m & -m).bit_length() - 1
        x = m >> v
        S += v
        out.append((S, x))
    return out


def tape_bits(S, x, width):
    """Absolute-position bit array [0, width): consumed cells count as 0."""
    a = np.zeros(width, np.uint8)
    b = x.bit_length()
    hi = min(width, S + b)
    if hi > S:
        raw = np.unpackbits(
            np.frombuffer(x.to_bytes((b + 7) // 8, "little"), np.uint8),
            bitorder="little")[: hi - S]
        a[S:hi] = raw
    return a


def fig_lightcone():
    rng = random.Random(77)
    BITS, J, T = 1200, 600, 430
    n0 = rng.getrandbits(BITS - 2) | (1 << (BITS - 1)) | 1
    n1 = n0 ^ (1 << J)
    r0, r1 = run_tapes(n0, T), run_tapes(n1, T)
    T = min(len(r0), len(r1))
    width = BITS + int(LOG23 * T) + 40
    X = np.zeros((T, width), np.uint8)
    div_row = None
    tops = []
    for r in range(T):
        S0, x0 = r0[r]
        S1, x1 = r1[r]
        X[r] = tape_bits(S0, x0, width) ^ tape_bits(S1, x1, width)
        if div_row is None and S0 != S1:
            div_row = r
        nz = np.nonzero(X[r])[0]
        if len(nz) and (div_row is None):
            tops.append((r, nz[-1]))
    # measured slope of the wedge top before divergence
    rs = np.array([t[0] for t in tops[5:]])
    ps = np.array([t[1] for t in tops[5:]])
    slope = np.polyfit(rs, ps, 1)[0] if len(rs) > 10 else float("nan")
    img = X[:, ::-1]                    # MSB left
    fig, ax = plt.subplots(figsize=(13.5, 6.4), dpi=145)
    ax.imshow(img, cmap="inferno", vmin=0, vmax=1, interpolation="nearest",
              aspect="auto")
    # overlay: front and predicted cone top (display coords: col = width-1-p)
    rr = np.arange(T)
    for p0, lab, c in ((BITS, "MSB front (seed top + 1.585 r)", "#39d353"),
                       (J, "cone top (flipped bit + 1.585 r)", "#00d5ff")):
        ax.plot(width - 1 - (p0 + LOG23 * rr), rr, color=c, lw=1.1, ls="--")
        ax.text(width - 1 - (p0 + LOG23 * min(T - 1, 360)) - 10,
                min(T - 1, 360), lab, color=c, fontsize=9, ha="right")
    if div_row:
        ax.axhline(div_row, color="#ff2d6f", lw=1.4)
        ax.text(6, div_row - 6, "the LeastEdge reads the flipped bit: the "
                "rhythm forks and the WHOLE future rewrites",
                color="#ff2d6f", fontsize=10)
    ax.set_xlabel("tape position (MSB left)")
    ax.set_ylabel("odd step")
    ax.set_xticks([])
    fig.suptitle("[real-CA] the bulk light cone: one bit flipped at position "
                 "%d of a %d-bit tape, XOR of the two real runs (bright = "
                 "cells that differ).\nThe influence wedge climbs at "
                 "measured %.4f cells/step (log2 3 = %.4f) - EXACTLY "
                 "parallel to the front: the bulk can never catch the left "
                 "edge.\nBelow, the wedge floor stays pinned at the flipped "
                 "bit until the sea arrives at step %s." %
                 (J, BITS, slope, LOG23, div_row), fontsize=11)
    out = os.path.join(IMG, "collatz-bulk-lightcone.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out, "| slope=%.4f vs log2(3)=%.4f, fork at row %s"
          % (slope, LOG23, div_row))


def crystal_word(d, copies):
    """The repeating 2-adic word of 1/d (period ord_2(d)), `copies` times."""
    q = 1
    t = 2 % d
    while t != 1:
        t = 2 * t % d
        q += 1
    blk = ((1 << q) - 1) // d           # word of the fraction 1/d
    w = 0
    for i in range(copies):
        w |= blk << (i * q)
    return w, q


def fig_gliders():
    W5, q5 = crystal_word(5, 80)        # 3 = 2^3 mod 5:  phase velocity 3
    W13, q13 = crystal_word(13, 27)     # 3 = 2^4 mod 13: phase velocity 4
    s5, s13 = 520, 860
    n = (W13 << s13) | (W5 << s5) | 1
    T = 300
    rows = run_tapes(n, T)
    T = len(rows)
    width = n.bit_length() + int(LOG23 * T) + 20
    M = np.zeros((T, width), np.uint8)
    for r in range(T):
        S, x = rows[r]
        M[r] = tape_bits(S, x, width)
    # measured phase velocity in each band: best cyclic shift row->row+1
    def phase_v(band_lo, band_hi, q):
        best = []
        for r in range(8, 100):
            a, b = M[r, band_lo:band_hi], M[r + 1, band_lo:band_hi]
            sc = [(np.mean(a == np.roll(b, -k)), k) for k in range(q)]
            best.append(max(sc)[1])
        vals, cnts = np.unique(best, return_counts=True)
        return int(vals[np.argmax(cnts)])
    v5 = phase_v(s5 + 40, s5 + 280, q5)
    v13 = phase_v(s13 + 40, s13 + 280, q13)
    img = M[:, ::-1]
    fig, ax = plt.subplots(figsize=(13.5, 8.4), dpi=145)
    fig.subplots_adjust(bottom=0.30)
    ax.imshow(img, cmap="Purples_r", vmin=0, vmax=1, interpolation="nearest",
              aspect="auto")
    for p0, lab, c in ((s5, "d=5 band base", "#0a6b28"),
                       (s13, "d=13 band base", "#b00040")):
        ax.axvline(width - 1 - p0, color=c, lw=1.0, ls=":")
        ax.text(width - 1 - p0 - 6, T * 0.97, lab, color=c, fontsize=9,
                rotation=90, va="bottom")
    ax.text(width - 1 - (s5 + 150), 40,
            "d=5 crystal: stripes at %d cells/step (3 = 2^3 mod 5)" % v5,
            color="#0a6b28", fontsize=10,
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="none"))
    ax.text(width - 1 - (s13 + 150), 150,
            "d=13 crystal: stripes at %d cells/step (3 = 2^4 mod 13)" % v13,
            color="#b00040", fontsize=10,
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="none"))
    ax.set_xlabel("tape position (MSB left)")
    ax.set_ylabel("odd step")
    ax.set_xticks([])
    # crisp insets: first 56 rows of each band, real cells
    for (lo, ttl, x0, col) in ((s5 + 60, "d=5 band, rows 0-55: slope 3",
                                0.14, "#0a6b28"),
                               (s13 + 60, "d=13 band, rows 0-55: slope 4",
                                0.56, "#b00040")):
        axi = fig.add_axes([x0, 0.035, 0.30, 0.16])
        axi.imshow(M[:56, lo:lo + 130][:, ::-1], cmap="Purples_r",
                   vmin=0, vmax=1, interpolation="nearest", aspect="auto")
        axi.set_xticks([]); axi.set_yticks([])
        for sp in axi.spines.values():
            sp.set_color(col)
        axi.set_title(ttl, fontsize=8.5, color=col, pad=2)
    fig.suptitle("[real-CA] bulk gliders, alive: two x3 traveling crystals "
                 "mid-tape on a %s-bit tape, hundreds of cells from either "
                 "edge.\nEach band's texture translates rigidly at its own "
                 "phase velocity (3 = 2^k mod d), racing its 1.585 growth "
                 "envelope; where the lower\nband's envelope reaches the "
                 "upper band, the carries braid them into a mixing wedge."
                 % "{:,}".format(n.bit_length()), fontsize=11)
    out = os.path.join(IMG, "collatz-bulk-gliders.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out, "| measured phase velocities: d5=%d (predict 3), "
          "d13=%d (predict 4)" % (v5, v13))


def main():
    fig_lightcone()
    fig_gliders()


if __name__ == "__main__":
    main()
