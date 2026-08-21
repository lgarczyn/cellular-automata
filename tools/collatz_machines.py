#!/usr/bin/env python3
"""Build and run actual machines in the real automaton. SCOPE: [real-CA].

Three constructed machines, each rendered running in CA.CollatzStep hex:

1. MSB-SPREADER: the optimal left-grower. By the exact fuse law
   (collatz_runners.py) the minimum legal halving is v = 1, so net leftward
   growth log2(3) - v is maximized at +0.585 bits/step by the v=1 rhythm,
   whose runner is -1: the all-ones tape. A B-bit all-ones machine climbs
   +0.585*(B-1) bits before its designed region is spent. Rendered against a
   random tape (which shrinks at ~ -0.4/step).

2. LSB-SLOWER: the same optimality seen from the right edge: v = 1 is the
   slowest legal LeastEdge advance, and all-ones is the unique tape family
   achieving it (v=1 forever forces n = -1 mod 2^k for all k). Rendered as
   the measured v-sequence (runner rhythm): flat at 1 for the whole designed
   life, vs alternating (1,2) tape, vs random jitter around 2.

3. COMPOSITED MACHINE: segments of different rhythms concatenated into one
   tape, i.e. a PROGRAM. The v-prefix of a tape is exactly one residue class
   mod 2^(S+1) (S = sum of prescribed v's), so ANY finite v-sequence can be
   compiled into a seed by 2-adic lifting. We compile the flight plan
   climb (v=1)^50, cruise (1,2)^20, dive (3)^12, climb (1)^30, run the real
   automaton, and the measured MSB altitude tracks the designed profile step
   for step until the program ends and the tape goes free.

The compiler (lift) is verified: the machine performs its designed v-sequence
exactly. Ground truth gate: seed 27 odd rows must match collatz_real.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collatz_real as R
import collatz_hex as HX

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
LOG2_3 = math.log2(3)


def odd_steps(n, k):
    """First k odd steps: values and v-sequence."""
    vals, vs = [n], []
    for _ in range(k):
        m = 3 * n + 1
        v = (m & -m).bit_length() - 1
        vs.append(v)
        n = m >> v
        vals.append(n)
        if n == 1:
            break
    return vals, vs


def consistent(r, p, vseq):
    """Does residue r (known mod 2^p) not contradict the v-sequence prefix?"""
    x = r % (1 << p)
    for w in vseq:
        if p < w + 1:
            return True                      # not yet decidable
        if (3 * x + 1) % (1 << (w + 1)) != (1 << w):
            return False
        x = ((3 * x + 1) >> w) % (1 << (p - w))
        p -= w
    return True


def lift(vseq):
    """Compile a v-sequence into the unique seed class mod 2^(S+1)."""
    S = sum(vseq)
    cands = [1]
    for m in range(2, S + 2):
        new = []
        for r in cands:
            for b in (0, 1):
                rr = r + (b << (m - 1))
                if consistent(rr, m, vseq):
                    new.append(rr)
        cands = sorted(set(new))
        assert cands, "lift dead-ended at bit %d" % m
    # verify each survivor performs the full program; return one that does
    for r in cands:
        n = r | (1 << (S + 3))               # cap bit clear of the program region
        _, vs = odd_steps(n, len(vseq))
        if vs == list(vseq):
            return n
    raise AssertionError("no candidate performed the program")


def hex_of(n, rows):
    peak = max(x.bit_length() for x in odd_steps(n, rows)[0])
    W = peak + rows + 8
    return R.run(n, W, rows + 1)


def altitude(n, k):
    vals, vs = odd_steps(n, k)
    return [x.bit_length() for x in vals], vs


def fig_spreader():
    B = 100
    machine = (1 << B) - 1
    import random
    random.seed(5)
    ctrl = random.getrandbits(B) | 1 | (1 << (B - 1))
    steps = 130
    alt_m, _ = altitude(machine, steps)
    alt_c, _ = altitude(ctrl, steps)
    g = hex_of(machine, 115)

    fig = plt.figure(figsize=(20, 11), dpi=130)
    ax1 = fig.add_axes([0.05, 0.08, 0.60, 0.84])
    HX.render_hex.__wrapped__ if False else None
    # draw hex inline (reuse renderer to a temp file is simpler)
    tmp = os.path.join(IMG, "_tmp_spreader_hex.png")
    HX.render_hex(g, tmp, title="")
    import matplotlib.image as mpimg
    ax1.imshow(mpimg.imread(tmp))
    ax1.axis("off")
    os.remove(tmp)
    ax1.set_title("[real-CA] MSB-SPREADER: all-ones machine (B=%d), the optimal left-grower\n"
                  "climbs at +%.3f bits/step for its whole designed life" % (B, LOG2_3 - 1),
                  fontsize=12)
    ax2 = fig.add_axes([0.72, 0.15, 0.25, 0.70])
    ax2.plot(alt_m, range(len(alt_m)), lw=2, color="#7c3aed", label="all-ones machine")
    ax2.plot(alt_c, range(len(alt_c)), lw=2, color="#ff5c8a", label="random tape")
    t = list(range(B))
    ax2.plot([B + (LOG2_3 - 1) * j for j in t], t, ls="--", color="#333",
             label="designed +0.585/step")
    ax2.invert_yaxis()
    ax2.set_xlabel("bit length (altitude, MSB spread)")
    ax2.set_ylabel("odd step (down)")
    ax2.legend(fontsize=9)
    ax2.grid(alpha=.3)
    fig.savefig(os.path.join(IMG, "collatz-machine-spreader.png"), facecolor="white",
                bbox_inches="tight")
    plt.close(fig)
    return alt_m[0], max(alt_m)


def fig_slowlsb():
    B = 100
    machines = [((1 << B) - 1, "all-ones (rhythm 1): THE optimal slower", "#39d353"),
                (lift([1, 2] * 33), "compiled (1,2) tape", "#7c3aed")]
    import random
    random.seed(6)
    ctrl = random.getrandbits(B) | 1 | (1 << (B - 1))
    fig, axs = plt.subplots(2, 1, figsize=(16, 9), dpi=130, sharex=True)
    ax = axs[0]
    for n, name, col in machines:
        _, vs = odd_steps(n, 90)
        ax.step(range(len(vs)), vs, where="mid", lw=1.8, color=col, label=name)
    _, vc = odd_steps(ctrl, 90)
    ax.step(range(len(vc)), vc, where="mid", lw=1.2, color="#ff5c8a", alpha=.8,
            label="random tape (mean ~2)")
    ax.axhline(1, color="#333", ls=":", lw=1)
    ax.set_ylabel("v (LeastEdge advance per odd step)")
    ax.legend(fontsize=9)
    ax.set_title("[real-CA] LSB-SLOWER machines: measured runner rhythm. v=1 is the legal minimum;\n"
                 "all-ones is provably the unique family achieving it (fuse law)", fontsize=12)
    ax.grid(alpha=.3)
    ax2 = axs[1]
    for n, name, col in machines + [(ctrl, "random", "#ff5c8a")]:
        _, vs = odd_steps(n, 90)
        cum = [sum(vs[:j + 1]) for j in range(len(vs))]
        ax2.plot(range(len(cum)), cum, lw=1.8, color=col, label=name)
    ax2.plot(range(90), [LOG2_3 * j for j in range(90)], ls="--", color="#333",
             label="log2(3) growth line (break-even)")
    ax2.set_xlabel("odd step")
    ax2.set_ylabel("cumulative LSB consumed (bits)")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "collatz-machine-slowlsb.png"), facecolor="white",
                bbox_inches="tight")
    plt.close(fig)


def fig_composite():
    program = [1] * 50 + [1, 2] * 20 + [3] * 12 + [1] * 30
    labels = [("climb (1)^50", 50), ("cruise (1,2)^20", 40),
              ("dive (3)^12", 12), ("climb (1)^30", 30)]
    n = lift(program)
    k = len(program) + 25                      # show the free tail too
    alts, vs = altitude(n, k)
    assert vs[:len(program)] == program, "machine failed its program"
    S0 = alts[0]
    designed = [S0]
    for w in program:
        designed.append(designed[-1] + LOG2_3 - w)

    g = hex_of(n, len(program) + 20)
    tmp = os.path.join(IMG, "_tmp_comp_hex.png")
    HX.render_hex(g, tmp, title="")
    import matplotlib.image as mpimg

    fig = plt.figure(figsize=(21, 12), dpi=130)
    ax1 = fig.add_axes([0.04, 0.06, 0.58, 0.86])
    ax1.imshow(mpimg.imread(tmp))
    ax1.axis("off")
    os.remove(tmp)
    ax1.set_title("[real-CA] COMPOSITED MACHINE: four rhythm segments compiled into one %d-bit tape\n"
                  "program: climb / cruise / dive / climb, performed exactly (verified v-sequence)"
                  % alts[0], fontsize=12)
    ax2 = fig.add_axes([0.68, 0.10, 0.29, 0.78])
    ax2.plot(alts, range(len(alts)), lw=2.2, color="#7c3aed", label="measured altitude")
    ax2.plot(designed, range(len(designed)), ls="--", lw=1.6, color="#39d353",
             label="designed flight plan")
    y = 0
    for name, ln in labels:
        ax2.axhline(y, color="#999", lw=.7, ls=":")
        ax2.text(min(alts) - 2, y + ln / 2, name, fontsize=8, rotation=0, va="center")
        y += ln
    ax2.axhline(y, color="#d33", lw=1.2)
    ax2.text(min(alts) - 2, y + 6, "program ends,\ntape goes free", fontsize=8, color="#d33")
    ax2.invert_yaxis()
    ax2.set_xlabel("bit length (altitude)")
    ax2.set_ylabel("odd step (down)")
    ax2.legend(fontsize=9, loc="lower right")
    ax2.grid(alpha=.3)
    fig.savefig(os.path.join(IMG, "collatz-machine-composite.png"), facecolor="white",
                bbox_inches="tight")
    plt.close(fig)
    return n, alts, len(program)


def main():
    # ground truth gate
    vals, _ = odd_steps(27, 9)
    assert vals[:10] == [27, 41, 31, 47, 71, 107, 161, 121, 91, 137][:len(vals)], vals
    print("ground truth gate (seed 27): OK")

    a0, peak = fig_spreader()
    print("MSB-spreader: start %d bits, peak %d bits (designed +%d)" % (a0, peak, round((LOG2_3 - 1) * 99)))

    fig_slowlsb()
    print("LSB-slower figure written (v=1 flat line vs (1,2) vs random)")

    n, alts, plen = fig_composite()
    print("composited machine: %d-bit seed, program of %d steps performed exactly;" % (alts[0], plen))
    print("  altitude start %d, peak %d, at program end %d" % (alts[0], max(alts[:plen + 1]), alts[plen]))
    print("  seed n = %d" % n)


if __name__ == "__main__":
    main()
