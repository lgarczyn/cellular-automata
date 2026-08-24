#!/usr/bin/env python3
"""The left edge of the hex graph is a readable instrument.

Run: python3 tools/collatz_edge.py [N]      (default 77031)

In the 3x+1/2 CA the left (MSB) edge advances 1 or 2 columns per row:
2 exactly when frac(log2 n) >= 2 - log2 3. Each row adds log2 3 to that
fraction, and the halvings subtract integers - which don't touch a
fractional part at all. So the entire LSB side (the halvings, the hash,
everything unpredictable about Collatz) is invisible to the left edge:
its growth pattern is the orbit coding of a pure circle rotation by
log2 3, perturbed only by the +1's drift of ~1/(3n ln 2) per row.

Two consequences, both implemented here:

  predict   the left-edge silhouette follows from the single real number
            frac(log2 n0), no trajectory computation - correct for ~90-97%
            of the trajectory (longer for larger n; it dies near the tail
            where n gets small and the +1 drift blows up).

  decode    conversely, the observed 1/2 growth pattern pins frac(log2 n)
            down: each row's symbol carves the circle, ~40 rows of the
            picture recover the number's magnitude to ~0.1%. You can read
            the mantissa of the input off a screenshot of the edge. (Only
            the mantissa: the low bits - the hash side - stay invisible.)

This is also a clean statement of how Collatz forgets: the LSB forgets its
input in one step, the MSB phase drifts by only ~1/n per step. The two
edges of the number are its fastest and slowest clocks.
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

K = math.log2(3)
T = 2 - K            # growth threshold: frac(log2 n) >= T means +2 columns


def growth_seq(n0):
    """True left-edge growth (1 or 2 columns) per row, from the trajectory."""
    seq = []
    val = n0
    while val != 1:
        seq.append(2 if (3 * val + 1).bit_length() - val.bit_length() == 2 else 1)
        t = 3 * val + 1
        while t % 2 == 0:
            t //= 2
        val = t
    return seq


def predict_seq(n0, rows):
    """Predicted growth from frac(log2 n0) alone, by pure rotation."""
    x = math.log2(n0) % 1.0
    out = []
    for _ in range(rows):
        out.append(2 if x >= T else 1)
        x = (x + K) % 1.0
    return out


def decode_phase(symbols):
    """Arcs of the circle consistent with an observed growth pattern."""
    arcs = [(0.0, 1.0)]
    for r, s in enumerate(symbols):
        lo, hi = (T, 1.0) if s == 2 else (0.0, T)
        off = (r * K) % 1.0
        a, b = (lo - off) % 1.0, (hi - off) % 1.0
        pre = [(a, b)] if a < b else [(a, 1.0), (0.0, b)]
        arcs = [(max(l1, l2), min(h1, h2))
                for l1, h1 in arcs for l2, h2 in pre
                if max(l1, l2) < min(h1, h2)]
    return arcs


def horizon(n0):
    """Rows until the rotation prediction first disagrees with reality."""
    t = growth_seq(n0)
    p = predict_seq(n0, len(t))
    return next((i for i, (a, b) in enumerate(zip(t, p)) if a != b), len(t)), len(t)


def main():
    n0 = int(sys.argv[1]) if len(sys.argv) > 1 else 77031
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    true = growth_seq(n0)
    pred = predict_seq(n0, len(true))
    mis, total = horizon(n0)
    print("%d: rotation predicts the left edge for %d of %d rows (%.0f%%)"
          % (n0, mis, total, 100 * mis / total))

    for R in (10, 20, 40):
        arcs = decode_phase(true[:R])
        width = sum(h - l for l, h in arcs)
        mid = (arcs[0][0] + arcs[0][1]) / 2
        print("decode from %2d rows: phase interval width %.1e, center %.6f (true %.6f)"
              % (R, width, mid, math.log2(n0) % 1.0))
    bits = n0.bit_length() - 1
    est = 2 ** (bits + (arcs[0][0] + arcs[0][1]) / 2)
    print("=> magnitude read off the picture: %.0f (true %d, error %.2f%%)"
          % (est, n0, 100 * abs(est - n0) / n0))

    import random
    random.seed(3)
    sizes, fracs = [], []
    for p in range(5, 15):
        fr = []
        for _ in range(40):
            n = random.randrange(10 ** p, 2 * 10 ** p) | 1
            m, t = horizon(n)
            fr.append(m / t)
        sizes.append(p)
        fracs.append(sorted(fr)[20])

    edge_t = [0] + [sum(true[:i + 1]) for i in range(len(true))]
    edge_p = [0] + [sum(pred[:i + 1]) for i in range(len(pred))]
    fig, axs = plt.subplots(1, 2, figsize=(17, 7), dpi=140)
    axs[0].plot([-e for e in edge_t], range(len(edge_t)), lw=1.6, color="#5470c6", label="actual left edge")
    axs[0].plot([-e for e in edge_p], range(len(edge_p)), lw=1.0, ls="--", color="#d03020", label="pure rotation from frac(log2 n)")
    axs[0].axhline(mis, color="gray", lw=0.8, ls=":")
    axs[0].text(-edge_t[-1] * 0.98, mis + 2, "first mismatch (row %d of %d)" % (mis, total), fontsize=9)
    axs[0].invert_yaxis()
    axs[0].set_xlabel("left-edge column (columns grow leftward)")
    axs[0].set_ylabel("row")
    axs[0].legend()
    axs[0].set_title("the MSB edge of %d, predicted without the trajectory" % n0)
    axs[1].plot(sizes, [100 * f for f in fracs], "o-", color="#5470c6")
    axs[1].set_xlabel("log10(n)")
    axs[1].set_ylabel("median % of trajectory predicted")
    axs[1].set_ylim(0, 100)
    axs[1].set_title("prediction horizon grows with n\n(the +1 drift is ~1/n per row)")
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-edge.png"))


if __name__ == "__main__":
    main()
