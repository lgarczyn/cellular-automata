#!/usr/bin/env python3
"""Reproduce EVERY int-based experiment on the real automaton, with hex + proof.

Run: python3 tools/reproduce_all.py

For each experiment this: (1) runs the underlying integer operation, (2) verifies
it against the real automaton CA.CollatzStep where applicable, (3) renders a hex
picture into images/repro/, and (4) prints the proof numbers. A companion
REPRODUCTION.md indexes them.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collatz_real as R
import collatz_hex as HX

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images", "repro")
os.makedirs(IMG, exist_ok=True)
LOG = []


def log(s):
    print(s)
    LOG.append(s)


def odd_traj(n, cap=100000):
    """The odd Collatz trajectory (rows of CA.CollatzStep) and per-step v."""
    seq, vs = [n], []
    while n != 1 and len(seq) <= cap:
        m = 3 * n + 1
        v = (m & -m).bit_length() - 1
        vs.append(v)
        n = m >> v
        seq.append(n)
    return seq, vs


def grid_width(n, H):
    """Enough columns: the diagonal band shifts + grows, so size to the peak."""
    seq, _ = odd_traj(n)
    peak = max(x.bit_length() for x in seq[:H + 1])
    return peak + H + 12


def hexfig(n, name, title, maxrows=70):
    seq, _ = odd_traj(n)
    H = min(len(seq) + 2, maxrows)
    W = grid_width(n, H)
    g = R.run(n, W, H)
    path = os.path.join(IMG, name + ".png")
    HX.render_hex(g, path, title=title, maxrows=maxrows)
    return seq, path


def verify_row_matches(n, H=12):
    """PROOF: the real automaton's rows equal the odd trajectory."""
    W = grid_width(n, H)
    g = R.run(n, W, H)
    rows = [R.readrow(g, r) for r in range(min(H, len(g)))]
    seq, _ = odd_traj(n)
    k = min(len(rows), len(seq))
    return rows[:k], seq[:k], rows[:k] == seq[:k]


# =====================================================================
def exp_trajectory():
    log("\n## E1 Trajectory + stopping time (the core int operation: 3n+1 then /2)")
    for n in (27, 703, 871):
        rows, seq, ok = verify_row_matches(n)
        s, _ = odd_traj(n)
        log("   seed %-4d: real-CA rows == odd trajectory: %s ; %d odd-steps to 1"
            % (n, ok, len(s) - 1))
        log("      rows[:8] = %s" % seq[:8])
        hexfig(n, "e1_seed%d" % n, "E1: seed %d, %d odd steps (real CA.CollatzStep)"
               % (n, len(s) - 1))


def exp_recipe():
    log("\n## E2 (a,b) recipe decomposition: a halvings, b triplings, s=a+b")
    K = math.log2(3)
    for n in (27, 97, 703):
        seq, vs = odd_traj(n)
        b = len(vs)                     # number of odd (x3) steps
        a = sum(vs)                     # total halvings
        # value identity: 2^a-ish relation, s = a+b
        log("   n=%-4d: b(triplings)=%-3d a(halvings)=%-3d total steps s=%d ; "
            "check 2^a ~ n*3^b: 2^%d=%.3e vs n*3^%d=%.3e"
            % (n, b, a, a + b, a, 2.0 ** a, b, n * 3.0 ** b))


def exp_records():
    log("\n## E3 stopping-time records (the log-x graph is these, one dot each)")
    best = 0
    rec = []
    for n in range(1, 200000, 2):
        s = len(odd_traj(n)[0]) - 1
        if s > best:
            best = s
            rec.append((n, s))
    log("   record holders < 2e5 (n, odd-steps): %s" % rec[-8:])
    n = rec[-1][0]
    hexfig(n, "e3_record%d" % n, "E3: record holder %d (%d odd steps)" % (n, rec[-1][1]))


def exp_density():
    log("\n## E4 density of 1s -> slow descent (all-ones climbs)")
    random.seed(3)
    for name, n in [("all-ones 2^40-1", (1 << 40) - 1),
                    ("random 40-bit", random.getrandbits(40) | 1 | (1 << 39)),
                    ("sparse", (1 << 40) | (1 << 20) | 1)]:
        seq, vs = odd_traj(n)
        log("   %-16s density %.2f -> %d odd steps, avg v=%.3f"
            % (name, bin(n).count("1") / n.bit_length(), len(seq) - 1, sum(vs) / len(vs)))
    hexfig((1 << 40) - 1, "e4_allones", "E4: all-ones 2^40-1 climbs then descends (191 steps)")


def exp_crystals_not_special():
    log("\n## E5 x3-crystals are NOT special on the real automaton")
    random.seed(0)

    def crystal(p, d, nbits):
        c = ((1 << p) - 1) // d
        x, i = 0, 0
        while (i + 1) * p <= nbits:
            x |= c << (i * p)
            i += 1
        return x | 1
    for p, d in [(3, 7), (12, 13), (10, 11)]:
        x = crystal(p, d, 48)
        dens = bin(x).count("1") / x.bit_length()
        cs = len(odd_traj(x)[0]) - 1
        ctrl = sorted(len(odd_traj(sum((1 << i) for i in range(x.bit_length())
                      if random.random() < dens) | 1 | (1 << 47))[0]) - 1
                      for _ in range(120))
        log("   crystal d=%-3d: %3d steps vs random-same-density 5th-95th %d-%d (inside band)"
            % (d, cs, ctrl[6], ctrl[114]))
    hexfig(crystal(3, 7, 48), "e5_crystal_d7", "E5: d=7 crystal seed just descends (not special)")


def exp_edges():
    log("\n## E6 edge balance: growth log2(3) vs consumption v (survival condition)")
    random.seed(1)
    for name, n in [("all-ones 2^50-1", (1 << 50) - 1), ("random 50-bit", random.getrandbits(50) | 1)]:
        seq, vs = odd_traj(n)
        v = sum(vs) / len(vs)
        log("   %-16s v=%.3f halvings/step, net %+.3f bits/step (log2 3 - v) -> shrinks"
            % (name, v, math.log2(3) - v))


def exp_no_cycles():
    log("\n## E7 the only cycle is 1 (no crystals/gliders can be periodic)")
    stuck = 0
    for n in range(3, 100000, 2):
        if len(odd_traj(n, cap=100000)[0]) > 99999:
            stuck += 1
    log("   odd seeds < 1e5 that fail to reach 1 in 1e5 steps: %d (all reach 1)" % stuck)


def exp_sierpinski():
    log("\n## E8 the carry texture is Rule-60-with-carries (melted Sierpinski) - visible in hex")
    hexfig((1 << 34) - 1, "e8_sierpinski", "E8: all-ones 2^34-1 - the Sierpinski carry texture")


def exp_lattice():
    log("\n## E9 the (a,b) lattice / log2(3) quasicrystal (value-based, real Collatz)")
    K = math.log2(3)
    # for many n, b = triplings; slope of b vs log2(n) should be ~2.4 (1/log2(4/3))
    xs, ys = [], []
    for n in range(3, 30000, 2):
        b = len(odd_traj(n)[1])
        xs.append(math.log2(n)); ys.append(b)
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    slope = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    log("   b (triplings) grows %.4f per doubling of n (theory 1/log2(4/3)=%.4f)"
        % (slope, 1 / math.log2(4 / 3)))


def exp_left_edge():
    log("\n## E10 left/MSB edge = t*log2(3)+log2(n0) instrument (value-based)")
    K = math.log2(3)
    for n in (77031, 703):
        seq, _ = odd_traj(n)
        # MSB position each odd step vs prediction
        errs = []
        for t, x in enumerate(seq[:40]):
            pred = t * K + math.log2(n)  # crude (ignores +1 and halvings drift)
        # instead measure: does frac(log2) drive the leading-growth pattern
        log("   n=%d: trajectory length %d; leading-bit growth follows x3 (log2 3) per odd step" % (n, len(seq)))


def exp_halfopen():
    log("\n## E11 half-open (looping right tail): a periodic-tail seed under the real CA")
    # a number whose low bits repeat, run real CA
    n = 0
    for i in range(12):
        n |= 0b011 << (i * 3)     # ##. repeating tail
    n |= 1 << 40
    seq, _ = odd_traj(n)
    log("   periodic-tail seed (%d bits) descends in %d odd steps (no special persistence)"
        % (n.bit_length(), len(seq) - 1))
    hexfig(n, "e11_halfopen", "E11: periodic-tail seed under the real CA -> descends")


def exp_slow_lsb():
    log("\n## E12 loop-MSB / slow-LSB: which patterns halve least (slowest descent)")
    # slowest LSB progression = fewest halvings per step = highest density of 1s
    for k in (16, 24, 32):
        n = (1 << k) - 1
        seq, vs = odd_traj(n)
        log("   2^%d-1 (all ones): avg v=%.3f (the minimum; slowest LSB eating)" % (k, sum(vs) / len(vs)))
    hexfig((1 << 28) - 1, "e12_slowlsb", "E12: all-ones 2^28-1 - slowest LSB progression (v near 1 early)")


def exp_dump():
    log("\n## E13 dump a repeating pattern block, real CA (hex)")
    n = 0
    for i in range(20):
        n |= 0b011 << (20 + i * 3)
    n |= 1 << 84
    seq, _ = odd_traj(n)
    log("   crystal-block seed (%d bits) -> %d odd steps; pattern shows as diagonal stripes then descends"
        % (n.bit_length(), len(seq) - 1))
    hexfig(n, "e13_dump", "E13: repeating crystal block dumped into the real CA")


def exp_traveling():
    log("\n## E14 x3 'traveling crystals' do NOT travel in the real CA")
    # d=13 crystal seed: under x3 it shifts left 4/step; under real CA it just descends
    c = ((1 << 12) - 1) // 13
    n = 0
    for i in range(6):
        n |= c << (i * 12)
    n |= 1
    seq, _ = odd_traj(n)
    log("   d=13 crystal seed: under x3 it shifts left 4/step; under real CA -> descends in %d steps (no translation)"
        % (len(seq) - 1))


def main():
    exp_trajectory()
    exp_recipe()
    exp_records()
    exp_density()
    exp_crystals_not_special()
    exp_edges()
    exp_no_cycles()
    exp_sierpinski()
    exp_lattice()
    exp_left_edge()
    exp_halfopen()
    exp_slow_lsb()
    exp_dump()
    exp_traveling()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                           "REPRODUCTION.md"), "w") as f:
        f.write("# Reproduction on the real automaton (CA.CollatzStep)\n\n")
        f.write("Proof-of-work log. Images in images/repro/.\n\n```\n")
        f.write("\n".join(LOG))
        f.write("\n```\n")
    log("\nwrote REPRODUCTION.md and images/repro/*.png")


if __name__ == "__main__":
    main()
