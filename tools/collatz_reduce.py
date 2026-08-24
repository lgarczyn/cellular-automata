#!/usr/bin/env python3
"""Throwing numbers away and watching the picture refuse to change.

Run: python3 tools/collatz_reduce.py [N]      (default 10^7)

Four different ways of deleting most of the inputs:

  irreducible  exact identities between residue classes. For n = 2^k*t + r,
               running until k halvings are done always lands on 3^j*t + B
               after k+j steps, with (j, B) fixed by (k, r). Classes sharing a
               (j, B) have step counts differing by a constant, so one of them
               determines the other. Keep one representative per (j, B).
  leaves       leaves of the odd tree m -> (3m+1)/2^v, which are exactly the
               odd multiples of 3: a predecessor is (2^v*m - 1)/3, needing
               2^v*m = 1 mod 3, which has no solution when 3 divides m.
  toggle       draw by XOR rather than by accumulation, so a cell survives only
               if it was hit an odd number of times.
  sieve        draw each trajectory once (see collatz_sieve.c).

Every one of them keeps the picture. That is the point: the structure is not
an artifact of the redundancy, it comes from the (a, b) recipe lattice.
"""

import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collatz import HERE, IMAGES, chunks, occupancy, steps


def reduce_class(k, r):
    """Run n = 2^k*t + r until k halvings are done; return the (j, B) it lands on."""
    A, B, h, j = 1 << k, r, 0, 0
    while h < k:
        if B % 2 == 0:
            A >>= 1
            B >>= 1
            h += 1
        else:
            A *= 3
            B = 3 * B + 1
            j += 1
    return j, B


def irreducible_mask(levels=20):
    """Residues mod 2^levels that no smaller-or-equal class already determines."""
    seen, surv = {}, [0]
    print(" k   classes mod 2^k   surviving   density")
    for k in range(0, levels + 1):
        cur = []
        for r in (surv if k == 0 else [x for s in surv for x in (s, s + (1 << (k - 1)))]):
            key = reduce_class(k, r)
            if key in seen:
                continue
            seen[key] = k
            cur.append(r)
        surv = cur
        if k <= 4 or k == levels:
            print("%2d   %14d   %9d   %.5f   %s"
                  % (k, 1 << k, len(surv), len(surv) / (1 << k),
                     sorted(surv) if k <= 3 else ""))
    m = np.zeros(1 << levels, bool)
    m[np.array(surv)] = True
    return m


def verify_identities(n_max):
    """Spot-check the identities the enumeration claims, against real data."""
    mm = steps(n_max)
    S = lambda v: np.asarray(mm[np.asarray(v) - 1], np.int64)
    m = np.arange(1, n_max // 8)
    print("steps(2m)    == steps(m) + 1     : %s" % (S(2 * m) == S(m) + 1).all())
    print("steps(8m+5)  == steps(2m+1) + 2  : %s" % (S(8 * m + 5) == S(2 * m + 1) + 2).all())
    t = np.arange(1, n_max // 16)
    print("steps(16t+3) == steps(8t+1) + 1  : %s" % (S(16 * t + 3) == S(8 * t + 1) + 1).all())


def sieve_mask(n_max, mode):
    binary = os.path.join(HERE, "collatz_sieve")
    source = os.path.join(HERE, "collatz_sieve.c")
    if not os.path.exists(binary) or os.path.getmtime(source) > os.path.getmtime(binary):
        subprocess.run(["gcc", "-O3", "-o", binary, source], check=True)
    out = os.path.join(HERE, "collatz_%s_%d.bin" % (mode, n_max))
    if not os.path.exists(out):
        subprocess.run([binary, mode, str(n_max), out], check=True)
    return np.fromfile(out, dtype=np.uint64)


def build(n_max, irr, sieve, anti):
    """One pass over the data, filling an occupancy grid per selection rule."""
    NX = 3000
    NY = int(35 * np.log2(n_max)) + 60      # generous; cropped to the data when plotting
    xmax = np.log2(n_max)
    names = ["all n", "odd only", "irreducible", "leaves", "toggle", "sieve", "antichain"]
    H = {k: np.zeros((NY, NX), np.int32) for k in names}
    kept = dict.fromkeys(names, 0)
    bit = lambda arr, idx: ((arr[idx >> 6] >> (idx & 63).astype(np.uint64)) & np.uint64(1)).astype(bool)

    for _, n, s, log2n in chunks(n_max):
        gx = (log2n / xmax * (NX - 1)).astype(np.int32)
        gy = np.minimum(s, NY - 1)
        sel = {
            "all n": np.ones(len(n), bool),
            "odd only": (n & 1) == 1,
            "irreducible": irr[n & (len(irr) - 1)],
            "leaves": (n % 6) == 3,
            "toggle": np.ones(len(n), bool),          # parity applied afterwards
            "sieve": bit(sieve, n),
            "antichain": bit(anti, n),
        }
        for k, m in sel.items():
            np.add.at(H[k], (gy[m], gx[m]), 1)
            kept[k] += int(m.sum())
    H["toggle"] = (H["toggle"] % 2).astype(np.int32)
    return H, kept, xmax


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000_000
    os.makedirs(IMAGES, exist_ok=True)

    print("== exact redundancy between residue classes ==")
    irr = irreducible_mask(20)
    print()
    verify_identities(n_max)
    print()
    print("== trajectory sieves ==")
    sieve, anti = sieve_mask(n_max, "sieve"), sieve_mask(n_max, "antichain")
    print()

    H, kept, xmax = build(n_max, irr, sieve, anti)
    base = (H["all n"] > 0).sum()
    print("== what each rule costs the picture ==")
    for k in H:
        print("   %-12s %5.1f%% of numbers -> %6d cells (%.1f%% of the full picture)"
              % (k, 100 * kept[k] / n_max, (H[k] > 0).sum(), 100 * (H[k] > 0).sum() / base))

    order = ["all n", "odd only", "irreducible", "leaves", "toggle", "sieve", "antichain"]
    top = int(np.flatnonzero(H["all n"].sum(1) > 0).max()) + 10
    fig, axs = plt.subplots(2, 4, figsize=(26, 12), dpi=120)
    for ax, k in zip(axs.ravel(), order):
        ax.imshow(occupancy(H[k][:top]), origin="lower", aspect="auto",
                  extent=[0, xmax * np.log10(2), 0, top],
                  cmap=ListedColormap(["#0000ff"]), interpolation="nearest")
        ax.set_title("%s\n%.1f%% of numbers, %.0f%% of cells"
                     % (k, 100 * kept[k] / n_max, 100 * (H[k] > 0).sum() / base), fontsize=12)
        ax.set_xlabel("log10(Input #)")
        ax.set_ylabel("Iterations to 1")
    axs.ravel()[-1].axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES, "collatz-reductions.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
