#!/usr/bin/env python3
"""Portraits of the interesting seeds the big scan actually found.
SCOPE: [real-CA]. Hex renders are cell-level CA.CollatzStep runs.

  collatz-wild-aims.png     the most crystalline seeds in the entire
                            32-bit universe (exhaustive) + the best
                            64-bit random find: natural flashes, not
                            designed ones
  collatz-tipped.png        an affine-tipped champion: the real run
                            crystallizes where the pure x3 flow does not
                            (the +1 carry completes the aim)
  collatz-echo-closeup.png  the echo family at bit level: the rows at
                            exactly the convergent lags, with their
                            noise neighbors
"""
import glob
import os
import sys
from math import log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collatz_leftedge as L
from collatz_render_compose import grid_of, panel_fig, sea_front
import collatz_compose as C

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
SCAN = "/var/tmp/collatz-scratch/leftscan"


def load_hits(pattern):
    hits = []
    for path in glob.glob(os.path.join(SCAN, pattern)):
        for line in open(path):
            p = line.split()
            hits.append((int(p[0]),) + tuple(map(float, p[1:])))
    return hits


def fig_wild():
    e32 = sorted(load_hits("exh32_*.txt"), key=lambda h: -max(h[1], h[2]))
    r64 = sorted(load_hits("r64_*.txt"), key=lambda h: -max(h[1], h[2]))
    picks = [(e32[0], 40, "exhaustive champion of ALL 2^31 odd 32-bit seeds"),
             (e32[1], 40, "exhaustive runner-up (32-bit)"),
             (r64[0], 60, "best of 2,000,000,000 random 64-bit seeds")]
    grids, caps, fronts, walls, notes = [], [], [], [], []
    for (h, T, label) in picks:
        n = h[0]
        run, k, P = L.aim_general(n, T, pbits=8)
        rows, vs = C.run_int(n, T)
        grids.append(grid_of(n, min(T, len(vs))))
        fronts.append(sea_front(vs))
        walls.append([n.bit_length() - 1])
        notes.append([(k, "the natural flash: P=%s at step %d" % (bin(P)[2:], k),
                       "#b00040")])
        caps.append("%s:  n = %d  (%d bits). Nobody designed it: its "
                    "mantissa happens to hit P=%s at step %d (constant "
                    "field %d bits). Scan scores: tape %.1f, front %.1f "
                    "bits of evidence."
                    % (label, n, n.bit_length(), bin(P)[2:], k, run,
                       h[1], h[2]))
    panel_fig(grids, caps,
              "[real-CA] the wild ones: natural crystallizations found by "
              "the exhaustive scan, not designed.\nEvery odd 32-bit seed "
              "was tested; these are the most crystalline moments that "
              "exist in that universe. Pink line = start column.",
              os.path.join(IMG, "collatz-wild-aims.png"),
              walls, notes, fronts, scale=0.075)


def bitmatrix(vals, W):
    out = np.zeros((len(vals), W), np.uint8)
    for i, v in enumerate(vals):
        b = v.bit_length()
        assert b >= W, "row thinner than window"
        top = v >> (b - W)
        for j in range(W):
            out[i, j] = (top >> (W - 1 - j)) & 1
    return out


def fig_tipped():
    """The cleanest tipping specimen: the 18-bit exhaustive champion.
    Its mantissa aims at P=1 from BELOW (2^g - eps), so the pure flow shows
    all-ones rows; the accumulated +1 carries tip the value over the power
    of 2 and the real machine shows all-zeros rows instead - crystallized
    either way, but with opposite polarity, and the real field lasts longer.
    """
    n, k, T, W = 145471, 10, 17, 14
    xs, ms = [], []
    x, m3 = n, n
    for r in range(1, T + 1):
        mm = 3 * x + 1
        x = mm >> ((mm & -mm).bit_length() - 1)
        m3 *= 3
        if r >= k - 2:
            xs.append(x)
            ms.append(m3)
    Mr, Msyn = bitmatrix(xs, W), bitmatrix(ms, W)
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.6), dpi=150)
    for ax, M, t in [(axes[0], Mr, "REAL run (with the +1 carries)"),
                     (axes[1], Msyn, "pure x3 flow (no +1)"),
                     (axes[2], (Mr != Msyn).astype(np.uint8),
                      "difference (white = cells that differ)")]:
        ax.imshow(M, cmap="gray" if t.startswith("diff") else "Purples_r",
                  vmin=0, vmax=1, interpolation="nearest", aspect="equal")
        ax.set_title(t, fontsize=10)
        ax.set_yticks(range(len(xs)))
        ax.set_yticklabels(["step %d" % r for r in range(k - 2, T + 1)],
                           fontsize=7.5)
        ax.set_xticks([])
        ax.axhline(2 - 0.5, color="#ff2d6f", lw=1.2)
        ax.axhline(2 + 0.5, color="#ff2d6f", lw=1.2)
    fig.suptitle("[real-CA] the affine tipping, cell by cell: n = %d (the "
                 "18-bit exhaustive champion), aim P=1 at step k=%d from "
                 "BELOW.\nPure x3 lands at 2^g - eps: rows of ONES (light). "
                 "The +1 carries tip it over the power of 2: the REAL rows "
                 "are ZEROS (dark).\nSame crystal, opposite polarity - and "
                 "visible only in the real machine's frame." % (n, k),
                 fontsize=10.5)
    fig.tight_layout(rect=[0, 0, 1, 0.80])
    out = os.path.join(IMG, "collatz-tipped.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_echo_closeup():
    K = 40
    LAGS = [665, 15601, 190537]
    T = K + LAGS[-1] + 4
    thick = int(0.43 * T) + 400
    n = ((1 << thick) // 3**K) | 1
    targets = {}
    want = {K: "flash"}
    for m in LAGS:
        for d in (-1, 0, 1):
            want[K + m + d] = (m, d)
    x = n
    for r in range(1, T + 1):
        mm = 3 * x + 1
        x = mm >> ((mm & -mm).bit_length() - 1)
        if r in want:
            b = x.bit_length()
            targets[r] = x >> (b - 48)
    rows, labels, marks = [], [], []
    rows.append(targets[K]); labels.append("step 40  THE FLASH"); marks.append(True)
    for m in LAGS:
        for d in (-1, 0, 1):
            rows.append(targets[K + m + d])
            labels.append("step 40%+d%+d" % (m, d) if d else
                          "step 40+%s  ECHO" % "{:,}".format(m))
            marks.append(d == 0)
    M = bitmatrix(rows, 48)
    fig, ax = plt.subplots(figsize=(12.5, 5.2), dpi=150)
    ax.imshow(M, cmap="Purples_r", vmin=0, vmax=1, interpolation="nearest",
              aspect="equal")
    for i, mk in enumerate(marks):
        if mk:
            ax.add_patch(plt.Rectangle((-0.5, i - 0.5), 48, 1, fill=False,
                                       edgecolor="#39d353", lw=1.8))
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xticks([])
    ax.set_xlabel("leading 48 bits of the row (MSB left; dark = 0)")
    ax.set_title("[real-CA] the echoes at bit level (one real run, %s odd "
                 "steps, %d-bit tape).\nAt EXACTLY the convergent lags the "
                 "leading bits collapse back to the flash's constant field "
                 "(green boxes);\none step to either side is generic river. "
                 "The +190,537 echo carries 22 constant bits." %
                 ("{:,}".format(T), thick), fontsize=10.5)
    fig.tight_layout()
    out = os.path.join(IMG, "collatz-echo-closeup.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def main():
    fig_wild()
    fig_tipped()
    fig_echo_closeup()


if __name__ == "__main__":
    main()
