#!/usr/bin/env python3
"""Composable blocks in the real CA: left edge + repeating word + right edge.
SCOPE: [real-CA]. Design tool: exact 2-adic rationals; every claim is then
realized as an actual integer tape and run with the real dynamics (rows =
CA.CollatzStep rows, cross-checked cell-by-cell against collatz_real.run).

The three building blocks of a growing pattern:

  left edge   the free MSB front (mantissa of 3^T * top word) - it grows into
              the void at log2(3) cells/step no matter what sits below it.
  bulk word   a spatially periodic texture. Its interior evolves under pure x3
              at fixed tape positions (the +1 carries never reach it), so the
              word must be an x3-cycle: block value A on the ring 2^q - 1.
  right edge  the termination motif where the word meets the LeastEdge, and
              the halving rhythm it produces there.

A word + its termination IS a 2-adic rational x (eventually periodic
expansion = rational with odd denominator). The rhythm at the right edge is
the Collatz orbit of x, and "the pattern persists" = x is on a CYCLE of the
Collatz map on rationals:  x = c / (2^S - 3^l)  for a v-sequence of length l
summing to S. Spread-left (growth) means v_bar = S/l < log2(3), i.e.
2^S < 3^l: the denominator is NEGATIVE - the rational is a negative 2-adic,
Lou's "we are in the middle of a giant number", made literal.

This module: (1) enumerate all such cycles for l <= LMAX, (2) realize each as
an integer tape and verify the rhythm locks in the real system, (3) compose
blocks A-over-B with a wall and measure the handoff: does the rhythm cross the
wall into A's own cycle (composition), some other cycle (persistence only), or
generic decay?  (4) hex renders in collatz_render_compose.py.
"""
import sys
from fractions import Fraction
from math import log2

sys.path.insert(0, __import__("os").path.dirname(__file__))
import collatz_real as R

LOG23 = log2(3)


def v2(n):
    return (n & -n).bit_length() - 1


def rat_step(x):
    """One odd Collatz step on a 2-adic rational (odd denominator)."""
    y = 3 * x + 1
    v = v2(y.numerator)
    return y / 2**v, v


def cycle_from_vseq(vs):
    """The unique rational cycling with rhythm vs, or None if not realized."""
    l, S = len(vs), sum(vs)
    c = 0
    pref = 0
    for i, v in enumerate(vs):
        c += 3 ** (l - 1 - i) * 2**pref
        pref += v
    den = 2**S - 3**l
    x0 = Fraction(c, den)
    x, got = x0, []
    for _ in range(l):
        x, v = rat_step(x)
        got.append(v)
    if x != x0 or got != list(vs):
        return None
    return x0


def ord2(d):
    """Multiplicative order of 2 mod d (d odd >= 1)."""
    if d == 1:
        return 1
    q, t = 1, 2 % d
    while t != 1:
        t = 2 * t % d
        q += 1
    return q


def expansion(x, k):
    """Low k 2-adic digits of rational x as an integer in [0, 2^k)."""
    p, d = x.numerator, x.denominator
    return (p * pow(d, -1, 2**k)) % 2**k


def word_of(x):
    """(preperiod digits string, period q, block int, density) of x's tail."""
    d = x.denominator
    q = ord2(d)
    depth = 4 * q + 64
    e = expansion(x, depth)
    bits = [(e >> i) & 1 for i in range(depth)]
    t = 0
    while any(bits[t + i] != bits[t + q + i] for i in range(depth - t - 2 * q)):
        t += 1
    blk = sum(bits[t + i] << i for i in range(q))
    dens = bin(blk).count("1") / q
    pre = "".join(str(b) for b in bits[t - 1 :: -1]) if t else ""
    return pre, q, blk, dens


class Block:
    def __init__(self, vs):
        self.vs = tuple(vs)
        self.l, self.S = len(vs), sum(vs)
        self.vbar = self.S / self.l
        self.growth = LOG23 - self.vbar
        self.x = cycle_from_vseq(vs)
        if self.x is None:
            return
        self.den = self.x.denominator
        self.pre, self.q, self.blk, self.dens = word_of(self.x)
        # all rationals on the cycle (the word's phase family)
        self.cycle = [self.x]
        y = self.x
        for _ in range(self.l - 1):
            y, _ = rat_step(y)
            self.cycle.append(y)

    def name(self):
        return "x=%s v=%s" % (self.x, ",".join(map(str, self.vs)))


def enumerate_blocks(lmax=7):
    """All growing rational cycles with minimal period <= lmax, deduped."""
    seen = {}
    for l in range(1, lmax + 1):
        for S in range(l, int(LOG23 * l) + 1):

            def parts(rem, k):
                if k == 1:
                    yield (rem,)
                    return
                for first in range(1, rem - (k - 1) + 1):
                    for rest in parts(rem - first, k - 1):
                        yield (first,) + rest

            for vs in parts(S, l):
                x0 = cycle_from_vseq(vs)
                if x0 is None:
                    continue
                b = Block(vs)
                key = frozenset(b.cycle)
                if len(key) < l:        # repeat of a shorter cycle
                    continue
                if key not in seen:
                    seen[key] = b
    return sorted(seen.values(), key=lambda b: (b.l, b.vbar, b.x))


# ---------------------------------------------------------------- real runs

def run_int(n, max_steps):
    """Real-CA rows (verified = odd Collatz steps): returns (rows, vseq)."""
    rows, vs = [n], []
    for _ in range(max_steps):
        if n <= 1:
            break
        m = 3 * n + 1
        v = v2(m)
        n = m >> v
        rows.append(n)
        vs.append(v)
    return rows, vs


def rhythm_lock(vs, cyc_vs):
    """Longest prefix of vs matching some rotation of cyc_vs, in steps."""
    best = 0
    l = len(cyc_vs)
    for r in range(l):
        rot = cyc_vs[r:] + cyc_vs[:r]
        k = 0
        while k < len(vs) and vs[k] == rot[k % l]:
            k += 1
        best = max(best, k)
    return best


def realize_and_verify(b, copies=8):
    """Integer tape = b's word stacked; check the rhythm locks as predicted."""
    M = b.q * copies + len(b.pre)
    n = expansion(b.x, M)
    if n % 2 == 0:
        n += 1  # cannot happen for a cycle rational (odd), guard anyway
    steps = int(M / b.vbar) + 4 * b.l
    rows, vs = run_int(n, steps)
    lock = rhythm_lock(vs, list(b.vs))
    predicted = int((M - len(b.pre)) / b.vbar) - b.l
    return M, n, lock, predicted


# ------------------------------------------------------------- composition

def tail_int(b, kbits):
    """kbits digits of b's pure periodic word tail (phase 0)."""
    return expansion(Fraction(-b.blk, 2**b.q - 1), kbits)


def compose(a, b, mb_extra=0, abits=None):
    """Integer tape: [a's words] over wall over [b's full block]."""
    MB = b.q * 8 + len(b.pre) + mb_extra
    if abits is None:
        abits = max(280, 12 * a.q)
        abits += (-abits) % a.q          # whole number of words
    low = expansion(b.x, MB)
    n = (tail_int(a, abits) << MB) | low
    return n, MB, abits


def wall_rational(a, b, mb_extra=0):
    """The exact 2-adic the composed tape realizes (B truncated, A infinite)."""
    MB = b.q * 8 + len(b.pre) + mb_extra
    return Fraction(expansion(b.x, MB)) + 2**MB * Fraction(-a.blk, 2**a.q - 1)


def predict_handoff(a, b, mb_extra=0, cap=800):
    """Exact rational orbit of the composed 2-adic: which cycle basin is the
    wall in?  Returns ('A'|'F'|'other'|'open', transient odd steps past wall).
    """
    z = wall_rational(a, b, mb_extra)
    MB = b.q * 8 + len(b.pre) + mb_extra
    acyc = set(a.cycle)
    cum = 0
    wall = None
    seen = {}
    for i in range(cap):
        if wall is not None:
            if z in acyc:
                return "A", i - wall
            if z == -1:
                return "F", i - wall
            if z in seen:
                return "other", seen[z] - wall
            seen[z] = i
        z, v = rat_step(z)
        cum += v
        if wall is None and cum >= MB:
            wall = i + 1
            if z in acyc:
                return "A", 0
    return "open", None


def handoff(a, b, mb_extra=0):
    """Run the composed integer tape in the real system; classify the rhythm
    that emerges past the wall.  'A' = a's own cycle rhythm locks while a's
    tape lasts (true composition), 'F' = fuse rhythm (v=1) locks instead,
    'decay' = neither: the wall scrambled it.  trans = odd steps between the
    wall crossing and the lock."""
    n, MB, abits = compose(a, b, mb_extra)
    return handoff_n(a, b, n, MB, abits)


def handoff_n(a, b, n, MB, abits):
    steps = int(MB / b.vbar) + abits + 60
    rows, vs = run_int(n, steps)
    cum, wall_step, exhaust = 0, None, len(vs)
    for i, v in enumerate(vs):
        cum += v
        if wall_step is None and cum >= MB:
            wall_step = i + 1
        if cum >= MB + abits:
            exhaust = i
            break
    if wall_step is None:
        return None
    p1 = rhythm_lock(vs, list(b.vs))
    # honest lock: the rhythm must match from t CONTINUOUSLY until the
    # designed tape is exhausted (slack for the crumbling top), not just
    # for a short coincidental stretch
    after = vs[wall_step:exhaust]
    slack = 2 * a.l + 6
    need = max(3 * a.l, 12)

    def locks(pattern_l, test):
        end = len(after) - slack
        for t in range(max(0, end - need)):
            if end - t >= need and test(after[t:end]):
                return t
        return None

    avs = list(a.vs)
    trans = locks(a.l, lambda seg: rhythm_lock(seg, avs) >= len(seg))
    cls = "A" if trans is not None else None
    if cls is None and a.x != -1:
        trans = locks(1, lambda seg: all(x == 1 for x in seg))
        if trans is not None:
            cls = "F"
    if cls is None:
        cls = "decay"
    return dict(n=n, MB=MB, abits=abits, wall=wall_step, p1lock=p1, cls=cls,
                trans=trans, vs=vs, rows=rows, exhaust=exhaust)


# ------------------------------------------------- the designed splice

def splice(a, b, periods=10, adepth=400):
    """Seamless A-over-B: instead of a raw cut, compute the exact preimage of
    a's cycle under `periods` full periods of b's rhythm.  The runner law
    forces the low digits to be b's word (b keeps its identity and rhythm);
    above the wall sits a's x3-history dressing, which anneals into a's pure
    word exactly when the LeastEdge arrives: transient 0 by construction.
    Returns (n, S, wall digits agreement with b's word)."""
    vs = list(b.vs) * periods
    S = sum(vs)
    z = a.x
    for v in reversed(vs):
        z = (z * 2**v - 1) / 3
        assert v2((3 * z + 1).numerator) == v
    M = S + adepth
    n = expansion(z, M)
    # how many low digits agree with b's own expansion?
    eb = expansion(b.x, M)
    agree = v2((n - eb) | (1 << M))
    return n, S, agree


def splice_check(a, b, periods=10):
    n, S, agree = splice(a, b, periods)
    steps = len(list(b.vs)) * periods + 30 * a.l + 40
    rows, vs = run_int(n, steps)
    w = len(b.vs) * periods
    okB = vs[:w] == list(b.vs) * periods
    okA = rhythm_lock(vs[w:], list(a.vs))
    return dict(n=n, S=S, agree=agree, okB=okB, alock=okA, vs=vs, rows=rows,
                wall=w)


# ------------------------------------------------------------------- main

def crosscheck_cell_level(n, steps=12):
    """Run the actual cell CA on n and compare rows with integer rows."""
    W = n.bit_length() + 2 * steps + 8
    g = R.run(n, W, steps + 1)
    got = [R.readrow(g, r) for r in range(steps + 1)]
    want, _ = run_int(n, steps)
    return got[: len(want)] == want


def zoo_table(blocks):
    print("=== the block zoo: growing rational cycles, l <= 7 ===")
    print("%-3s %-14s %-6s %-7s %-14s %-5s %-8s %s"
          % ("l", "rhythm", "vbar", "growth", "x", "q",
             "density", "right-edge motif"))
    for b in blocks:
        print("%-3d %-14s %-6.3f %-+7.3f %-14s %-5d %-8.3f %s"
              % (b.l, ",".join(map(str, b.vs)), b.vbar, b.growth,
                 str(b.x), b.q, b.dens, b.pre or "(pure word)"))


def reps_of(blocks):
    """One block per denominator, smallest word first (matrix readability)."""
    reps, seen = [], set()
    for b in sorted(blocks, key=lambda b: (b.q, b.l, b.vbar)):
        if b.den not in seen and b.q <= 24:
            seen.add(b.den)
            reps.append(b)
    return reps


def main():
    blocks = enumerate_blocks(7)
    zoo_table(blocks)

    print("\n=== solo realization: rhythm lock in the real system ===")
    bad = 0
    for b in blocks:
        M, n, lock, pred = realize_and_verify(b)
        if lock < pred:
            bad += 1
            print("SHORT %-28s M=%d lock=%d predicted>=%d"
                  % (b.name(), M, lock, pred))
    print("all %d blocks lock as predicted" % len(blocks) if not bad
          else "%d blocks FAILED to lock" % bad)

    reps = reps_of(blocks)
    fuse = next(b for b in reps if b.x == -1)
    n_demo, _, _ = compose(reps[2], fuse)
    print("\ncell-level crosscheck on a composed tape:",
          "OK" if crosscheck_cell_level(n_demo) else "FAIL")

    print("\n=== raw-cut composition: A over wall over B, all wall phases ===")
    print("cell: A<phases locking a's cycle> F<fuse instead> d<decay>"
          " tmin<shortest transient> | P: exact-rational prediction agrees?")
    names = ["d%d/%s" % (b.den, ",".join(map(str, b.vs))) for b in reps]
    width = max(len(s) for s in names) + 2
    print(" " * 18 + "".join(s.ljust(18) for s in names))
    mism, tot = [], 0
    for ia, a in enumerate(reps):
        line = names[ia].ljust(18)
        for b in reps:
            na = nf = nd = 0
            tmin = None
            for mb_extra in range(b.q):
                h = handoff(a, b, mb_extra=mb_extra)
                p, ptrans = predict_handoff(a, b, mb_extra=mb_extra)
                if h is None:
                    continue
                tot += 1
                if p != h["cls"] and not (h["cls"] == "decay"
                                          and p in ("other", "open")):
                    # give the real tape room to outlast the predicted
                    # transient, then re-measure
                    if ptrans is not None:
                        big = min(6000, 3 * ptrans + 600)
                        big += (-big) % a.q
                        n2, MB2, _ = compose(a, b, mb_extra, abits=big)
                        h2 = handoff_n(a, b, n2, MB2, big)
                        # our classifier only names 'A' and 'F' locks, so a
                        # predicted 'other' cycle shows up as measured decay
                        if h2 and (h2["cls"] == p or
                                   (p == "other" and h2["cls"] == "decay")):
                            continue
                    mism.append((a.den, b.den, mb_extra, p, ptrans,
                                 h["cls"], h["trans"]))
                if h["cls"] == "A":
                    na += 1
                    tmin = h["trans"] if tmin is None else min(tmin, h["trans"])
                elif h["cls"] == "F":
                    nf += 1
                else:
                    nd += 1
            cell = "A%d F%d d%d" % (na, nf, nd)
            if tmin is not None:
                cell += " t%d" % tmin
            line += cell.ljust(18)
        print(line)
    print("prediction (exact 2-adic wall rational orbit) vs real run: "
          "%d/%d unexplained disagreements (after giving the tape room to "
          "outlast the predicted transient)" % (len(mism), tot))
    for m in mism[:20]:
        print("  A=d%s B=d%s phase=%d predicted=%s(t=%s) measured=%s(t=%s)"
              % m)

    print("\n=== the designed splice: computed wall, transient 0 ===")
    for a, b in [(reps[2], fuse), (fuse, reps[2]), (reps[3], reps[2]),
                 (reps[2], reps[3]), (reps[4], reps[5]),
                 (blocks[-1], reps[2])]:
        if a.q > 40 or b.q > 40:
            continue
        r = splice_check(a, b)
        print("A=d%-4s over B=d%-4s: S=%-4d wall-digit agreement with B's "
              "word=%-4d B-rhythm exact=%s A-lock=%d steps after wall"
              % (a.den, b.den, r["S"], r["agree"], r["okB"], r["alock"]))


if __name__ == "__main__":
    main()
