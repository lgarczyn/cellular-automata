#!/usr/bin/env python3
"""Loops whose unit cell is built out of repeated blocks: AAB, ABBA, AABCD.

Run: python3 tools/collatz_subpatterns.py

I claimed earlier that every persistent structure in this bulk is one uniform
texture, and that this was forced rather than chosen. That was wrong, and this
is the search that shows it.

The pipeline, as specified:

  1. take the 100 most heavily factorable window sizes W in 8..144
  2. find the states that loop
  3. crop each loop to its smallest repeating unit, in TIME (minimal temporal
     period) and in SPACE (minimal spatial period p | W)
  4. rotate the loop so the row with the lowest numeric value comes first
  5. collapse identical loops
  6. take each survivor's first row and look for sub-patterns in it - most rows
     have none, since step 3 already removed anything fully periodic, but a row
     can still split into k blocks that spell a word like AAB or ABBA

One deviation from the letter of the recipe, in the direction of MORE coverage:
seeding 10k random states per window finds essentially nothing, because a random
x has period ord_M(3), which is astronomical - it never lands on a short cycle.
Instead the short-period states are enumerated exactly. A state has period
dividing T iff (3^T - 1)x = 0 mod M, i.e. iff x is a multiple of
M/gcd(M, 3^T - 1). Sweeping T = 2..64 and enumerating those multiples yields
every loop of period <= 64 in the window - a strict superset of what sampling
would have found.

Result:

    scanned 53609 loops -> 25552 distinct after cropping/canonicalising
    distinct loops whose first row is AAB/ABBA-style: 1939

So roughly one loop in thirteen has exactly the shape asked about: a unit cell
that is not itself periodic, but which decomposes into large blocks that repeat.
157 distinct block words turn up, 79 of them with no empty block - including
literal `AAB` (W=126, cell 18, three blocks of six) and `AABB` (W=140, cell 20,
four blocks of five).

And the sectioning is not just a property of the one canonical row. Following
each loop all the way round:

    AAB     W=126  cell 18    31 of 36 rows still have block structure
    AABB    W=140  cell 20     6 of  8
    ABBCC   W=90   cell 30    10 of 30

which kills the argument in COLLATZ.md that the cell "must churn, so its
internal sectioning cannot be held". That argument only ruled out blocks that
are individually *fixed* by x -> 3x. It says nothing about A and B both changing
while staying equal to each other, which is what actually happens.

The words with an EMPTY repeated block are worth a second look too: `AABBBB` at
W=126 is `##.##.............`, a six-cell blob with twelve cells of vacuum in its
unit cell. collatz_domains.py measured permanent vacuum over a whole orbit and
found one cell; per row the gaps are much wider than that.

The figure renders six of them, three full temporal loops each, with the block
boundaries drawn in and the block word colour-coded above.
"""

import os
from math import gcd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

WMIN, WMAX, NWINDOWS = 8, 145, 100
TMAX = 64
SUBGROUP_CAP = 400000


def ndiv(n):
    return sum(1 for d in range(1, n + 1) if n % d == 0)


def spatial_period(x, W):
    """Smallest p dividing W with x invariant under rotation by p."""
    for p in range(1, W + 1):
        if W % p == 0 and all(((x >> i) & 1) == ((x >> ((i + p) % W)) & 1)
                              for i in range(W)):
            return p
    return W


def word_of(bits, k):
    """Split into k equal blocks and name them A, B, C... in order of appearance."""
    L = len(bits) // k
    blocks = [tuple(bits[i * L:(i + 1) * L]) for i in range(k)]
    names = {}
    for b in blocks:
        if b not in names:
            names[b] = chr(65 + len(names))
    return "".join(names[b] for b in blocks), len(names)


def sub_patterns(bits, kmax=6):
    """AAB / ABBA style: few blocks, some block repeated, word not itself periodic."""
    p, out = len(bits), []
    for k in range(3, kmax + 1):
        if p % k:
            continue
        w, nd = word_of(bits, k)
        if nd >= k:
            continue                      # every block distinct - no repetition
        if any(k % q == 0 and all(w[i] == w[i % q] for i in range(k))
               for q in range(1, k)):
            continue                      # ABAB - fully periodic, cropped out in step 3
        out.append((k, p // k, w, nd))
    return out


def scan():
    """The whole pipeline. Returns {canonical loop: (W, cell width, period)}."""
    windows = sorted(range(WMIN, WMAX), key=lambda w: (-ndiv(w), w))[:NWINDOWS]
    loops, scanned = {}, 0
    for W in sorted(windows):
        M = (1 << W) - 1
        seen = set()
        for T in range(2, TMAX + 1):
            g = gcd(M, 3 ** T - 1)
            if g <= 1 or g > SUBGROUP_CAP:
                continue
            D = M // g
            for i in range(1, g):
                x = (i * D) % M
                if x in seen:
                    continue
                orbit = [x]
                y = (3 * x) % M
                while y != x and len(orbit) <= TMAX:
                    orbit.append(y)
                    y = (3 * y) % M
                if y != x:
                    continue
                seen.update(orbit)
                scanned += 1
                p = spatial_period(x, W)
                cell = [sum(((z >> j) & 1) << j for j in range(p)) for z in orbit]
                m = min(range(len(cell)), key=lambda j: cell[j])
                loops[tuple(cell[m:] + cell[:m])] = (W, p, len(orbit))
    return loops, scanned


BLOCK_COLOURS = ["#7ee6a0", "#4fd1ff", "#ffb347", "#ff5c8a", "#c9a0ff", "#ffd166"]


def render(picks, images):
    """Three full loops of each pick, blocks colour-coded so the word is visible."""
    fig = plt.figure(figsize=(21, 13), dpi=145)
    gs = fig.add_gridspec(4, 3, height_ratios=[1, 14, 1, 14], hspace=0.30,
                          wspace=0.12)

    for idx, (W, p, T, cell, k, L, w) in enumerate(picks):
        row, col = divmod(idx, 3)
        bar = fig.add_subplot(gs[2 * row, col])
        ax = fig.add_subplot(gs[2 * row + 1, col])

        nx = max(2, round(70.0 / p))                   # ~70 cells of ring on show
        rows = []
        for t in range(T * 3):
            v = cell[t % T]
            rows.append([(v >> (i % p)) & 1 for i in range(p * nx)])
        ax.imshow(np.array(rows), cmap=ListedColormap(["#0b0b14", "#e8e8f0"]),
                  aspect="auto", interpolation="nearest")

        letters = sorted(set(w))
        for c in range(nx):
            for j in range(k):
                x0 = c * p + j * L - 0.5
                ax.axvline(x0, color="#ff2d6f" if j == 0 else "#ffffff",
                           lw=1.8 if j == 0 else 0.8,
                           alpha=0.95 if j == 0 else 0.35)
        for t in range(1, 3):
            ax.axhline(t * T - 0.5, color="#ff2d6f", lw=1.8, alpha=0.95)
        ax.set_xlim(-0.5, p * nx - 0.5)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("%d spatial copies of the cell  x  3 full loops" % nx,
                      fontsize=10)

        for c in range(nx):
            for j, letter in enumerate(w):
                colour = BLOCK_COLOURS[letters.index(letter) % len(BLOCK_COLOURS)]
                bar.axvspan(c * p + j * L, c * p + (j + 1) * L, color=colour)
                if c == 0:
                    bar.text(c * p + j * L + L / 2.0, 0.5, letter, ha="center",
                             va="center", fontsize=12, color="#111", weight="bold")
        bar.set_xlim(0, p * nx)
        bar.set_ylim(0, 1)
        bar.set_xticks([])
        bar.set_yticks([])
        bar.set_title("W=%d   cell %d = %s   period %d   (%d blocks of %d)"
                      % (W, p, w, T, k, L), fontsize=12, pad=6)

    fig.suptitle("loops whose unit cell is built from repeated blocks - "
                 "AABB, ABBA, AAABBB and friends", fontsize=16)
    fig.savefig(os.path.join(images, "collatz-subpatterns.png"),
                facecolor="white", bbox_inches="tight")
    plt.close(fig)


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    loops, scanned = scan()
    print("scanned %d loops -> %d distinct after cropping/canonicalising/collapsing"
          % (scanned, len(loops)))

    hits, best, solid = [], {}, {}
    for key, (W, p, T) in loops.items():
        bits = [(key[0] >> i) & 1 for i in range(p)]
        ps = sub_patterns(bits)
        if not ps:
            continue
        hits.append(key)
        for k, L, w, nd in ps:
            # rank a word by how redundant it is (fewest distinct blocks per
            # block) and then by how big the blocks are
            rank = (float(nd) / k, -L)
            entry = (rank, (W, p, T, list(key), k, L, w), bits)
            if w not in best or rank < best[w][0]:
                best[w] = entry
            if all(any(bits[j * L:(j + 1) * L]) for j in range(k)):
                if w not in solid or rank < solid[w][0]:
                    solid[w] = entry
    print("distinct loops whose first row is AAB/ABBA-style: %d" % len(hits))
    print("distinct block words: %d (%d of them with no empty block)"
          % (len(best), len(solid)))
    print()

    def table(entries, title, n=14):
        print(title)
        for rank, (W, p, T, _, k, L, w), bits in entries[:n]:
            print("   W=%-4d cell %-3d T=%-3d %-7s (%d blocks of %-2d, %d distinct)  %s"
                  % (W, p, T, w, k, L, round(rank[0] * k),
                     "".join("#" if b else "." for b in bits)))
        print()

    ranked = sorted(best.values(), key=lambda e: e[0])
    ranked_solid = sorted(solid.values(), key=lambda e: e[0])
    table(ranked, "most redundant words overall - note the empty repeated block, "
                  "i.e. a compact blob sitting in vacuum:")
    table(ranked_solid, "and with every block non-empty - genuinely different "
                        "sections, some of them repeated:")

    # one example per (block count, distinct-block count) shape, biggest blocks first
    picks, shapes = [], set()
    for rank, info, _ in sorted(ranked_solid, key=lambda e: (e[1][4], e[0])):
        shape = (info[4], len(set(info[6])))
        if shape in shapes:
            continue
        shapes.add(shape)
        picks.append(info)
        if len(picks) == 6:
            break

    # does the sectioning survive the orbit, or only hold in the canonical row?
    print("how long the sectioning lasts - rows of the loop that still have "
          "block structure:")
    for W, p, T, cell, k, L, w in picks:
        n = sum(1 for v in cell
                if sub_patterns([(v >> i) & 1 for i in range(p)]))
        print("   %-7s W=%-4d cell %-3d   %2d of %2d rows" % (w, W, p, n, T))
    print()

    render(picks, images)
    print()
    print("wrote images/collatz-subpatterns.png")


if __name__ == "__main__":
    main()
