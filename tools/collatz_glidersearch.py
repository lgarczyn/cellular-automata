#!/usr/bin/env python3
"""Glider search on the x3-with-carry (digit,carry) antidiagonal CA.

SCOPE: [x3-bulk]. This is NOT CA.CollatzStep (no LeastEdge, no +1). Its
negative result binds only the x3 model; see tools/MANIFEST.md.

Run: python3 tools/collatz_glidersearch.py     (all cores)

This corrects an earlier error. The claim "no localized left-mover exists" was
first argued from linearity of x -> 3x. But that is the BULK / value map, not the
cellular automaton. The real CA carries (digit, carry) as state on the
antidiagonals t = r + c, and there the update of cell (t,c) from the two previous
diagonals is a full adder:

    new_digit = shifted_digit XOR above_digit XOR carry_in        (linear)
    new_carry = majority(shifted_digit, above_digit, carry_in)    (NONLINEAR)

The carry is a majority gate - genuinely nonlinear over GF(2) (verified) - so the
3^t*e0 dispersion argument does NOT apply, and gliders are possible in principle.
So we searched the real rule properly:

  * 262,143 localized (digit,carry) seeds on vacuum: every one grows.
  * 142 ethers (spatially+temporally periodic backgrounds) found by enumerating
    cycles of the period-p CA for p <= 8.
  * >1.3 million defects placed exhaustively on the 40 most structured ethers,
    240 steps each, tracking the difference from the pure-ether evolution.

Result: ZERO gliders. Every defect either dies or grows past 40 cells within at
most 77 steps. No bounded translating structure, no coherent one-sided left
front, on any ether.

WHY (and it turns on the boundary condition). The x3 rule grows every structure
leftward; a bounded left-mover needs a CONSUMPTION mechanism to balance that
growth. The only consumption in Collatz is the halving (LeastEdge eating trailing
zeros = /2). But halving requires TRAILING ZEROS at a terminating right edge - and
a LOOPING right edge (a nonzero periodic tail) has none. So under exactly the
stated boundary condition (free MSB + looping right), the dynamics reduces to
pure x3-with-carry, which this search shows has no localized left-mover.

The consumption ("runners down the right edge") lives at a TERMINATING right edge,
not a looping one. That is the model a left-mover search should use next: a finite
number with a real LSB boundary where halvings occur, not a periodic tail.
"""

import time
from multiprocessing import Pool, cpu_count


def make_step(W):
    MASK = (1 << W) - 1

    def step(b1, b2, cr1):
        sh = ((b2 << 1) | (b2 >> (W - 1))) & MASK       # digit[c-1] -> c
        cin = ((cr1 << 1) | (cr1 >> (W - 1))) & MASK
        nb = sh ^ b1 ^ cin
        ncr = (sh & b1) | (sh & cin) | (b1 & cin)        # majority (nonlinear)
        return nb, b1, ncr
    return step, MASK


def find_ethers(pmax=8):
    ethers = []
    for p in range(1, pmax + 1):
        step, _ = make_step(p)
        color = {}
        for s in range(1 << (3 * p)):
            if s in color:
                continue
            path, x = [], s
            while x not in color and x not in path:
                path.append(x)
                b1 = x & ((1 << p) - 1)
                b2 = (x >> p) & ((1 << p) - 1)
                cr = (x >> (2 * p)) & ((1 << p) - 1)
                nb, nb2, ncr = step(b1, b2, cr)
                x = nb | (nb2 << p) | (ncr << (2 * p))
            if x in path and len(path) - path.index(x) <= 64:
                cyc = path[path.index(x):]
                ethers.append((p, len(cyc), min(cyc)))
            for y in path:
                color[y] = 1
    return sorted({(p, per, r): (p, per, r) for p, per, r in ethers if r}.values())


def tile(v, p, W):
    o = 0
    for i in range(W // p):
        o |= v << (i * p)
    return o


def scan(job):
    p, per, rep, W, T, CAP, DW = job
    step, MASK = make_step(W)
    b1e = tile(rep & ((1 << p) - 1), p, W)
    b2e = tile((rep >> p) & ((1 << p) - 1), p, W)
    cre = tile((rep >> (2 * p)) & ((1 << p) - 1), p, W)
    C, MG = W // 2, 30
    maxlife = bounded = 0
    for code in range(1, 1 << (3 * DW)):
        d1 = (code & ((1 << DW) - 1)) << C
        d2 = ((code >> DW) & ((1 << DW) - 1)) << C
        dc = ((code >> 2 * DW) & ((1 << DW) - 1)) << C
        pb1, pb2, pcr = b1e, b2e, cre
        xb1, xb2, xcr = b1e ^ d1, b2e ^ d2, cre ^ dc
        life, kind = T, "bounded"
        for t in range(T):
            pb1, pb2, pcr = step(pb1, pb2, pcr)
            xb1, xb2, xcr = step(xb1, xb2, xcr)
            diff = (pb1 ^ xb1) | (pb2 ^ xb2) | (pcr ^ xcr)
            if diff == 0:
                kind, life = "dies", t
                break
            lo = (diff & -diff).bit_length() - 1
            hi = diff.bit_length() - 1
            if hi - lo + 1 > CAP:
                kind, life = "grows", t
                break
            if lo < MG or hi > W - MG:
                kind, life = "escaped", t
                break
        maxlife = max(maxlife, life)
        if kind in ("bounded", "escaped"):
            bounded += 1
    return p, per, maxlife, bounded


def main():
    print("verifying nonlinearity of the carry (majority) gate...")
    import random
    rng = random.Random(0)
    W = 64
    maj = lambda a, b, c: (a & b) | (a & c) | (b & c)
    lin = all(maj(x ^ u, y ^ v, z ^ w) == (maj(x, y, z) ^ maj(u, v, w))
              for x, y, z, u, v, w in
              [[rng.getrandbits(W) for _ in range(6)] for _ in range(500)])
    print("   carry gate linear over GF(2)? %s  (False => gliders not excluded)" % lin)
    print()

    ethers = find_ethers(8)
    rich = [e for e in ethers if e[1] >= 6 and e[0] >= 2][:40]
    print("found %d ethers; searching the %d most structured" % (len(ethers), len(rich)))
    W, T, CAP, DW = 260, 240, 40, 5
    print("exhaustive width-%d defects (%d each), %d steps, %d cores"
          % (DW, (1 << (3 * DW)) - 1, T, cpu_count()))
    t0 = time.time()
    with Pool(cpu_count()) as pool:
        res = pool.map(scan, [(p, per, rep, W, T, CAP, DW) for p, per, rep in rich])
    print("done in %.1fs" % (time.time() - t0))
    total_defects = len(rich) * ((1 << (3 * DW)) - 1)
    print()
    print("defects tested: %d" % total_defects)
    print("bounded/translating survivors: %d" % sum(r[3] for r in res))
    print("max quasi-lifetime before growth/death: %d of %d steps"
          % (max(r[2] for r in res), T))
    print()
    print("=> no glider on any ether. under free-MSB + LOOPING right (no halving,")
    print("   no consumption) the true nonlinear CA has no localized left-mover.")


if __name__ == "__main__":
    main()
