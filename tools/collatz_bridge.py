#!/usr/bin/env python3
"""The bridge: does the x3-bulk composition atlas show up in the LeastEdge rhythm?

Run: /usr/bin/python3 tools/collatz_bridge.py            (full experiment, ~3 min, 16 cores)
     /usr/bin/python3 tools/collatz_bridge.py verify     (just the ground-truth checks)

SCOPE
  [real-CA]  The v-sequence measured here IS the LeastEdge rhythm of
             CA.CollatzStep: each display row is one odd step, and verify()
             checks on the actual grid (collatz_real.run) that the LeastEdge
             extends by exactly v columns per row (LE extent at row r ==
             cumulative v), that readrow reproduces the odd trajectory, and
             that a bit at original position p sits at the CONSTANT grid
             column p+1 (bulk structure is spatially static; the front moves,
             the crystal does not). The hex figure is the real automaton.
  [value]    The wedge/defect analysis reads bit patterns of the row values
             n_t, re-anchored by cumulative halvings V_t (original-frame
             position q = bit q - V_t of n_t). Rows are real-CA rows, so
             valid, but it is bit-string arithmetic, not tile-level
             (digit, carry) state. The cycle census on rationals -X/(2^p-1)
             is exact [value] arithmetic.
  [x3-bulk]  The charge law is used only to CLASSIFY pairs: width-L blocks
             A,B concatenate persistently under pure x3 iff A = B mod
             3^(v3(2^(2L)-1)); for the odd L used here that is A = B mod 3.
             Whether that law means anything in the real CA is the question,
             not an input.

SEEDS  domain geometry: low region = kA repeats of width-L block A (LSB side,
eaten first), then kB repeats of block B, then a single 1 as MSB cap; A odd so
the seed is odd; the A|B interface is at bit kA*L = constant grid column
kA*L + 1. tiling geometry: (A B) repeated as one width-2L cell.

FINDINGS (2026-08-21 run of this script; all numbers regenerate)

Q1 [real-CA rows] - a crystal low region produces a PERFECTLY structured
  rhythm while it is consumed; a random one does not. The A-phase v-sequence
  equals, step for step, the odd-map orbit of the 2-adic rational -A/(2^L-1)
  (exact for 180/180 crystal seeds, L=5,7,9, 240-bit regions), which is
  eventually periodic. Autocorrelation peak (lags 1..60): crystals 0.71 +-
  0.16 vs random 0.21 +- 0.04, Cohen's d = 4.9. Strict periodicity inside
  the observation window: 112/180 crystals vs 0/300 random (the rest have
  cycle period or transient longer than the ~120-step window - they still
  sit exactly on the deterministic ideal). Mean v barely differs (2.06 vs
  2.01): the signature is order, not rate.

Q2 [real-CA rows] - the A->B boundary is exact in the rhythm. The v-sequence
  diverges from the pure-A ideal at the first odd step whose halving window
  pokes past bit kA*L: bits-consumed-at-divergence minus kA*L has median +1,
  IQR 0..1, max 6 over 1888 pairs; divergence step minus predicted step
  (first t with V_t >= kA*L): median 0. A blind changepoint (break of the
  learned A-period) finds the same step in 1404/1404 of the pairs where the
  A-period is learnable. The rhythm knows where the wall is to the bit.

Q3 - does charge matter in the real CA? Three geometries, honest answer:
  mostly NO; every rhythm observable has |d| < 0.1.
  a) domain pairs A^40 B^60 (L=5 exhaustive 480, L=7 sampled 1408):
     - the interface radiates a DISORDER WEDGE (loss of L-periodicity)
       MSB-ward into the B region, visible in the real CA and in the hex
       render. Mean growth rate over pairs ~ log2(3) bits/step (per-A it
       varies: ~1.5 for A=00111, ~0.7 for the all-ones A), but it does NOT
       depend on charge: wedge extent when the front reaches the interface
       (L=5, 140-bit window): matched 117.8 +- 6.1 bits vs mismatched
       117.4 +- 6.1, d = -0.08 (L=7: d = -0.04). The wedge is the
       archimedean image of the consumed A-region (3^t * A-part) invading
       B - a universal mechanism, not the charge law. A^kA B^kB is NOT a
       true composition even in x3-bulk (collatz_truecomp: A^(k-1)B never),
       so the atlas in fact predicts no charge protection in this geometry,
       and indeed there is none.
     - because of the wedge, the post-boundary rhythm does NOT re-lock
       within a 300-bit B region (1888/1888 pairs); B-phase mean v is
       random-like: L=5 matched 2.026 vs mismatched 2.013 (d = -0.10),
       L=7 2.007 vs 2.013 (d = +0.04).
  b) relock experiment (small wedge: L=5 kA=12 kB=100, 480 pairs; L=7
     kA=9 kB=72, 1408 pairs): after the front crosses, the rhythm DOES
     re-lock onto a periodic cycle of the (2^L-1)-denominator family once
     the wedge bits are eaten. Relock fraction and delay after the
     boundary: L=5 matched 118/150, 109.1 +- 23.9 steps vs mismatched
     251/330, 106.7 +- 24.4 (d = -0.10); L=7 432/704, 105.6 +- 23.0 vs
     402/704, 106.0 +- 19.5 (d = +0.02). (Unrelocked pairs sit on cycles
     longer than the 60-step detector or still inside the transient.)
     Charge does not gate recovery; wedge size does.
  c) tiling (AB)^40, the geometry where matched charge IS a true x3
     composition (cell X = A|B<<L, matched <=> 3|X): consumption vbar
     matched 1.791 +- 0.227 (n=150) vs mismatched 1.793 +- 0.198 (n=329),
     d = +0.01; an exact cycle census of ALL width-p crystals -X/(2^p-1)
     (p = 5,7,9,10,12,14) shows eventual-cycle vbar is FLAT in v3(X)
     (e.g. p=10: 1.721 / 1.718 / 1.735 for v3 = 0 / 1 / 2+). No charge
     law of the rhythm exists even for true compositions. Curiosity found
     on the way: X=341 = (2^10-1)/3 makes the tail exactly -1/3, and 3n+1
     annihilates the whole 400-bit region in ONE step (v = 402) - the
     perfect fuse, and maximally mismatched.
  Census side-result [value]: among all 2^(p-1) width-p crystal rhythms,
  essentially the only negative (growing-side) cycle ever reached is
  all-ones -> -1 (v=1); every other crystal escapes to a positive cycle
  with vbar ~ 2 - one more face of "everything shrinks".

CONCLUSION  composition is loud in the rhythm (Q1: order; Q2: boundaries to
the bit), but the x3 CHARGE is a bulk/persistence quantity: in the real CA it
never registers in the LeastEdge rhythm (|d| <= 0.1 on rate, relock, or
transition, three geometries, ~2400 runs), and the structure-destroying wedge
at a domain wall is universal rather than charge-gated. What controls rhythm
recovery is the archimedean corruption band (the consumed region's image
spreads MSB-ward at ~log2(3) bits/step while the front eats at vbar), which
the front must chew through before the B-crystal rhythm reappears.

Figures: images/collatz-bridge-hex.png   (real-CA hex, matched vs mismatched,
                                          interface marked, wedge visible)
         images/collatz-bridge-wedge.png (mean defect maps + wedge growth)
         images/collatz-bridge-stats.png (Q1/Q2/Q3 statistics)
"""

import os
import sys
import math
import random
from fractions import Fraction
from multiprocessing import Pool

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collatz_real as R
import collatz_hex as HX

IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                      "images")

# validated categorical palette (dataviz skill): blue / red / yellow
C_MATCH = "#2a78d6"   # matched charge / crystal
C_MISS = "#e34948"    # mismatched charge / random
C_MARK = "#eda100"    # boundary markers
C_INK = "#52514e"

# ----------------------------------------------------------------- primitives

def v2(x):
    return (x & -x).bit_length() - 1


def v3(n):
    e = 0
    while n and n % 3 == 0:
        n //= 3
        e += 1
    return e


def compose_seed(A, B, L, kA, kB):
    Arep = sum(A << (j * L) for j in range(kA))
    Brep = sum(B << (j * L) for j in range(kB))
    return (1 << (L * (kA + kB))) | (Brep << (L * kA)) | Arep


def vseq(n, stopV):
    """[real-CA rows] LeastEdge rhythm: v per odd step until stopV bits eaten."""
    vs, V = [], 0
    while V < stopV and n > 1:
        t = 3 * n + 1
        v = v2(t)
        n = t >> v
        vs.append(v)
        V += v
    return vs


def crystal_ideal(A, L, T):
    """[real-CA rows] v-sequence of the infinite crystal A^inf: the odd map on
    the 2-adic rational -A/(2^L-1). Exact; a finite A^k seed follows it until
    cumulative v crosses the region."""
    x = Fraction(-A, (1 << L) - 1)
    vs = []
    for _ in range(T):
        y = 3 * x + 1
        num = y.numerator
        v = v2(num) if num else 1
        vs.append(v)
        x = y / (1 << v)
    return vs


def find_period(vs, pmax=60, skip=8):
    """Smallest P such that vs[skip:] is P-periodic. None if aperiodic."""
    tail = vs[skip:]
    n = len(tail)
    for P in range(1, pmax + 1):
        if n < 2 * P:
            break
        if all(tail[i] == tail[i + P] for i in range(n - P)):
            return P
    return None


def relock_point(vs, t_from, pmax=60):
    """Earliest t >= t_from such that vs[t:] is periodic to the end.
    Finds the tail period first, then scans backward. Returns (t, P) or None."""
    n = len(vs)
    tail_start = max(t_from, n - 100)
    P = find_period(vs[tail_start:], pmax=pmax, skip=0)
    if P is None or n - tail_start < 2 * P + 8:
        return None
    t = n - P
    while t - 1 >= t_from and vs[t - 1] == vs[t - 1 + P]:
        t -= 1
    if n - t < 2 * P + 8:
        return None
    return t, P


def charge_modulus(L):
    return 3 ** (v3((1 << (2 * L)) - 1) - v3((1 << L) - 1))


# ------------------------------------------------------------------- verify()

def verify():
    """[real-CA] ground truth: port check, LE-extent == cumulative v,
    constant-column bulk, v-seq == 2-adic ideal."""
    n, rows = 27, [27]
    for _ in range(6):
        t = 3 * n + 1
        n = t >> v2(t)
        rows.append(n)
    assert rows == [27, 41, 31, 47, 71, 107, 161], "PORT BROKEN"

    L, kA, kB = 5, 6, 6
    A, B = 0b11111, 0b10101
    n0 = compose_seed(A, B, L, kA, kB)
    H, W = 34, 120
    g = R.run(n0, W, H)
    vs, ns, m = [], [], n0
    for _ in range(H - 1):
        t = 3 * m + 1
        v = v2(t)
        m = t >> v
        vs.append(v)
        ns.append(m)
    V = [0]
    for v in vs:
        V.append(V[-1] + v)
    for r in range(H):
        nr = n0 if r == 0 else ns[r - 1]
        assert R.readrow(g, r) == nr, "row value mismatch at %d" % r
        lemax = max(c for c in range(W) if R.isLE(g[r][c]))
        assert lemax == V[r], "LE extent %d != cumulative v %d" % (lemax, V[r])
        # bulk is spatially static: original bit p lives at column p+1
        cb = kA * L + 1
        if V[r] < kA * L:
            cell = g[r][cb]
            assert cell is not None and not R.isLE(cell)
            assert cell["d"] == (nr >> (kA * L - V[r])) & 1, "column drift"
    # crystal rhythm == 2-adic ideal
    for LL, AA in ((5, 0b11111), (5, 0b10101), (7, 0b1011011)):
        k = 40
        seed = sum(AA << (j * LL) for j in range(k)) | (1 << (k * LL))
        ideal = crystal_ideal(AA, LL, 400)
        vv = vseq(seed, k * LL - LL)
        assert vv == ideal[:len(vv)], "2-adic ideal mismatch"
    print("verify: port OK; LE extent == cumulative v OK; constant-column "
          "bulk OK; crystal v-seq == 2-adic ideal OK")


# ------------------------------------------------- Q1: crystal vs random rhythm

Q1_BITS = 240      # low-region length in bits
Q1_MARGIN = 20


def q1_stats(vs):
    a = np.asarray(vs, dtype=float)
    mean = a.mean()
    c = a - mean
    denom = (c * c).sum()
    if denom < 1e-12:                     # constant rhythm (all-ones crystal)
        acmax = 1.0
    else:
        acmax = max(abs((c[:-k] * c[k:]).sum() / denom) for k in range(1, 61))
    return mean, acmax, find_period(vs)


def q1_worker(job):
    kind, L, A, seed = job
    if kind == "crystal":
        k = Q1_BITS // L
        low = sum(A << (j * L) for j in range(k))
        nbits = k * L
    else:
        rng = random.Random(seed)
        low = rng.getrandbits(Q1_BITS) | 1
        nbits = Q1_BITS
    vs = vseq((1 << nbits) | low, nbits - Q1_MARGIN)
    mean, acmax, P = q1_stats(vs)
    ideal_ok = None
    if kind == "crystal":
        ideal_ok = vs == crystal_ideal(A, L, len(vs))
    return kind, L, A, mean, acmax, P, ideal_ok, vs


def run_q1(pool):
    jobs = [("crystal", L, A, 0) for L in (5, 7)
            for A in range(1, 1 << L, 2)]
    rng = random.Random(7)
    jobs += [("crystal", 9, A, 0)
             for A in rng.sample(range(1, 1 << 9, 2), 100)]
    jobs += [("random", 0, 0, 1000 + i) for i in range(300)]
    return pool.map(q1_worker, jobs)


# ------------------------------- Q2/Q3a: domain pairs, changepoint and wedge

PAIR_CFG = {5: dict(kA=40, kB=60), 7: dict(kA=29, kB=43)}
DEF_LO, DEF_HI = 60, 140                 # defect window around the interface
TMAX_MAP = 170                           # defect-map time extent


def pair_worker(job):
    """One composed domain seed: rhythm + anchored defect (wedge) rows."""
    L, A, B = job
    cfg = PAIR_CFG[L]
    kA, kB = cfg["kA"], cfg["kB"]
    boundary = kA * L
    top = (kA + kB) * L
    n = compose_seed(A, B, L, kA, kB)
    vs, V = [], 0
    q0 = boundary - DEF_LO
    wmask = (1 << (DEF_LO + DEF_HI)) - 1
    defrows = []
    while V < top - 30 and n > 1:
        if V <= q0 and len(defrows) < TMAX_MAP:
            w = n >> (q0 - V)             # bit i of w = original-frame q0 + i
            defrows.append((w ^ (w >> L)) & wmask)
        t = 3 * n + 1
        v = v2(t)
        n = t >> v
        vs.append(v)
        V += v
    nb = (DEF_LO + DEF_HI + 7) // 8
    dm = np.zeros((len(defrows), DEF_LO + DEF_HI), dtype=np.uint8)
    for i, d in enumerate(defrows):
        dm[i] = np.unpackbits(
            np.frombuffer(d.to_bytes(nb, "little"), dtype=np.uint8),
            bitorder="little")[: DEF_LO + DEF_HI]
    if len(defrows):
        up = dm[-1][DEF_LO:]
        wedge = int(np.max(np.nonzero(up)[0]) + 1) if up.any() else 0
    else:
        wedge = -1
    m = charge_modulus(L)
    return dict(L=L, A=A, B=B, matched=(A % m == B % m), vs=vs, dm=dm,
                wedge=wedge, boundary=boundary, top=top)


def make_pairs():
    pairs = [(5, A, B) for A in range(1, 1 << 5, 2)
             for B in range(1, 1 << 5) if B != A]
    rng = random.Random(11)
    m7 = charge_modulus(7)
    for A in range(1, 1 << 7, 2):
        Bs = [B for B in range(1, 1 << 7) if B != A]
        matched = [B for B in Bs if B % m7 == A % m7]
        missed = [B for B in Bs if B % m7 != A % m7]
        for B in rng.sample(matched, 11) + rng.sample(missed, 11):
            pairs.append((7, A, B))
    return pairs


def analyze_pair(res, ideal_cache):
    """Changepoint observables against the pure-A 2-adic ideal."""
    L, A = res["L"], res["A"]
    vs = res["vs"]
    boundary, top = res["boundary"], res["top"]
    key = (A, L)
    if key not in ideal_cache:
        ideal_cache[key] = crystal_ideal(A, L, top + 40)
    ideal = ideal_cache[key]
    V = np.cumsum(vs)
    t_pred = int(np.searchsorted(V, boundary) + 1)       # first step past wall
    t_div = None
    for i, v in enumerate(vs):
        if v != ideal[i]:
            t_div = i + 1
            break
    if t_div is None:
        return None
    consumed = (V[t_div - 2] if t_div >= 2 else 0) + min(vs[t_div - 1],
                                                         ideal[t_div - 1])
    # blind changepoint: learn the A-period from the first 60% of the A phase
    nA = int(np.searchsorted(V, boundary * 0.6))
    P = find_period(vs[:nA]) if nA > 20 else None
    t_blind = None
    if P is not None:
        for i in range(8 + P, len(vs)):
            if vs[i] != vs[i - P]:
                t_blind = i + 1
                break
    inB = (V >= boundary + 40) & (V <= top - 40)
    vbarB = float(np.asarray(vs)[inB].mean()) if inB.any() else float("nan")
    rl = relock_point(vs, t_div - 1)
    return dict(t_pred=t_pred, t_div=t_div, t_blind=t_blind,
                delay_bits=int(consumed - boundary),
                delay_steps=int(t_div - t_pred),
                relocked=rl is not None, vbarB=vbarB)


# ------------------------------------- Q3b: relock experiment (small wedge)

RELOCK_CFG = {5: dict(kA=12, kB=100), 7: dict(kA=9, kB=72)}


def relock_worker(job):
    L, A, B = job
    cfg = RELOCK_CFG[L]
    kA, kB = cfg["kA"], cfg["kB"]
    boundary, top = kA * L, (kA + kB) * L
    vs = vseq(compose_seed(A, B, L, kA, kB), top - 30)
    V = np.cumsum(vs)
    t_bound = int(np.searchsorted(V, boundary)) + 1
    rl = relock_point(vs, t_bound - 1)
    m = charge_modulus(L)
    out = dict(L=L, A=A, B=B, matched=(A % m == B % m), delay=None, P=None,
               bits=None)
    if rl is not None:
        t_lock, P = rl
        out.update(delay=t_lock + 1 - t_bound, P=P,
                   bits=int(V[t_lock - 1] - boundary) if t_lock >= 1 else 0)
    return out


# ------------------------------------------- Q3c: tiling (AB)^k consumption

def tiling_worker(job):
    L, A, B = job
    X = A | (B << L)
    p = 2 * L
    k = 400 // p
    low = sum(X << (p * j) for j in range(k))
    vs = vseq(low | (1 << (p * k)), p * k - Q1_MARGIN)
    m = charge_modulus(L)
    return dict(A=A, B=B, X=X, matched=(A % m == B % m),
                vbar=float(np.mean(vs)), steps=len(vs),
                degenerate=(X * 3 == (1 << p) - 1))


# --------------------------------------- census: crystal cycles, exact [value]

def census_worker(job):
    p, X = job
    x = Fraction(-X, (1 << p) - 1)
    seen, vs, t = {}, [], 0
    while x not in seen and t < 3000:
        seen[x] = t
        y = 3 * x + 1
        num = y.numerator
        v = v2(num) if num else 1
        vs.append(v)
        x = y / (1 << v)
        t += 1
    if x not in seen:
        return None
    t0 = seen[x]
    cyc = vs[t0:]
    return p, X, t0, len(cyc), sum(cyc) / len(cyc), bool(x < 0)


def run_census(pool):
    jobs = [(p, X) for p in (5, 7, 9, 10, 12, 14)
            for X in range(1, 1 << p, 2)]
    return [r for r in pool.map(census_worker, jobs, chunksize=64)
            if r is not None]


# ------------------------------------------------------------------- figures

def cohens_d(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    sp = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1))
                   / max(len(a) + len(b) - 2, 1))
    return (a.mean() - b.mean()) / sp if sp > 0 else float("inf")


def fig_hex():
    """[real-CA] hex render: one matched and one mismatched composed seed,
    interface column marked, run until the B region is consumed."""
    L, kA, kB = 5, 8, 8
    A = 0b11111                           # all-ones: v=1 rhythm, charge 1
    demo = ((0b10011, "matched"), (0b10101, "mismatched"))
    panels = []
    for B, tag in demo:
        n0 = compose_seed(A, B, L, kA, kB)
        n, V, rows = n0, 0, 1
        while V < (kA + kB) * L + 10 and n > 1:
            t = 3 * n + 1
            v = v2(t)
            n = t >> v
            V += v
            rows += 1
        H = rows + 2
        W = (kA + kB) * L + 2 + int(H * 0.6) + 30
        g = R.run(n0, W, H)
        n, Vs = n0, [0]
        for _ in range(H - 1):
            t = 3 * n + 1
            v = v2(t)
            n = t >> v
            Vs.append(Vs[-1] + v)
        panels.append((g, Vs, B, tag, H, W))

    fig, axs = plt.subplots(2, 1, figsize=(24, 22), dpi=110)
    sqrt3 = math.sqrt(3)
    Rr = 0.5
    hexW = sqrt3 * Rr
    from matplotlib.patches import RegularPolygon
    from matplotlib.collections import PatchCollection
    for ax, (g, Vs, B, tag, H, W) in zip(axs, panels):
        patches, colors = [], []
        for r in range(H):
            cy = -r * 1.5 * Rr
            for c in range(W):
                col = HX.cell_color(g[r][c])
                if col is None:
                    continue
                cx = (W - 1 - c) * hexW + r * hexW / 2.0
                patches.append(RegularPolygon((cx, cy), numVertices=6,
                                              radius=Rr * 0.98, orientation=0))
                colors.append(col)
        ax.add_collection(PatchCollection(patches, facecolors=colors,
                                          edgecolors="#0b0b14", linewidths=0.25))
        # interface: constant grid column kA*L+1 -> slanted line in hex coords
        cb = kA * L + 1
        rs = [r for r in range(H) if Vs[r] <= kA * L]
        xs = [(W - 1 - cb - 0.5) * hexW + r * hexW / 2.0 for r in rs]
        ys = [-r * 1.5 * Rr for r in rs]
        ax.plot(xs, ys, color=C_MARK, lw=2.5, solid_capstyle="round", zorder=5)
        ax.annotate("A | B interface (bit %d)" % (kA * L),
                    xy=(xs[-1], ys[-1]), xytext=(xs[-1] - 16, ys[-1] - 4),
                    color=C_MARK, fontsize=13, ha="right",
                    arrowprops=dict(arrowstyle="-", color=C_MARK, lw=1.2))
        rcross = next(r for r in range(H) if Vs[r] > kA * L)
        ycross = -rcross * 1.5 * Rr
        ax.axhline(ycross, color=C_MARK, lw=1.0, ls=":", alpha=0.8)
        ax.autoscale_view()
        ax.text(ax.get_xlim()[0] + 1, ycross + 0.9,
                "front crosses the interface (row %d)" % rcross,
                color=C_MARK, fontsize=12)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("%s charge:  A=%s (x%d)   B=%s (x%d)   A mod 3 = %d, "
                     "B mod 3 = %d" % (tag, format(A, "05b"), kA,
                                       format(B, "05b"), kB, A % 3, B % 3),
                     fontsize=15, loc="left")
    fig.suptitle("[real-CA] CA.CollatzStep eating a composed tail  (L=%d, "
                 "MSB left, LeastEdge green, 1-digit purple, carry tinted)\n"
                 "right of the yellow line: the A crystal being eaten (v=1 "
                 "rhythm). left: the B region - and the disorder wedge the "
                 "consumed region's image (x3^t) drives into it, matched and "
                 "mismatched ALIKE: the wedge is universal, not charge-gated"
                 % L, fontsize=17)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = os.path.join(IMAGES, "collatz-bridge-hex.png")
    fig.savefig(path, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def fig_wedge(maps):
    """[value] mean defect maps (loss of L-periodicity, anchored frame) and
    wedge growth, matched vs mismatched, L=5 domain pairs."""
    (m_sum, m_cnt), (x_sum, x_cnt) = maps["m5"], maps["x5"]
    fig, axs = plt.subplots(1, 3, figsize=(21, 6.4), dpi=140)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("wb", ["#ffffff", C_MATCH])
    extent = (-DEF_LO, DEF_HI, m_sum.shape[0], 0)
    for ax, s, c, tag in ((axs[0], m_sum, m_cnt, "matched charge"),
                          (axs[1], x_sum, x_cnt, "mismatched charge")):
        dens = s / np.maximum(c, 1)
        dens[c == 0] = np.nan
        im = ax.imshow(dens, cmap=cmap, vmin=0, vmax=0.55, aspect="auto",
                       extent=extent, interpolation="nearest")
        ax.axvline(0, color=C_MARK, lw=2)
        ax.set_title("%s - mean defect density" % tag, fontsize=13)
        ax.set_xlabel("bits above the A|B interface (anchored frame)")
        ax.set_ylabel("odd step (front below interface)")
        ax.text(3, 12, "interface", color=C_MARK, fontsize=11, rotation=90)
    fig.colorbar(im, ax=axs[:2], shrink=0.85, label="P(bit q != bit q+L)")
    ax = axs[2]
    for s, c, col, tag, dy in ((m_sum, m_cnt, C_MATCH, "matched", 8),
                               (x_sum, x_cnt, C_MISS, "mismatched", -14)):
        dens = s / np.maximum(c, 1)
        T = int((c[:, 0] > 20).sum())
        w = []
        for t in range(T):
            up = dens[t, DEF_LO:]
            idx = np.nonzero(up > 0.08)[0]
            w.append(idx.max() + 1 if len(idx) else 0)
        ax.plot(range(T), w, color=col, lw=2)
        ax.annotate(tag, xy=(T - 1, w[-1]), xytext=(T - 30, w[-1] + dy),
                    color=col, fontsize=12)
    tt = np.arange(0, 80)
    ax.plot(tt, math.log2(3) * tt, color=C_INK, lw=1.2, ls="--")
    ax.text(47, math.log2(3) * 47 - 22, "slope log2(3)", color=C_INK,
            fontsize=11, rotation=38)
    ax.set_xlabel("odd step")
    ax.set_ylabel("wedge extent above interface (bits)")
    ax.set_title("wedge growth: the two curves coincide - charge-blind",
                 fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("[value, rows of real CA] the disorder wedge a domain wall "
                 "drives into the B region while the front eats A (L=5, mean "
                 "over pairs): identical for matched and mismatched charge",
                 fontsize=15)
    path = os.path.join(IMAGES, "collatz-bridge-wedge.png")
    fig.savefig(path, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def fig_stats(q1, pairstats, relocks, tilings, example):
    fig, axs = plt.subplots(2, 3, figsize=(21, 11), dpi=140)

    # (1) example v-sequences
    ax = axs[0][0]
    (vs_c, bstep), vs_r = example
    ax.step(range(1, len(vs_c) + 1), vs_c, where="mid", color=C_MATCH, lw=1.5)
    ax.step(range(1, len(vs_r) + 1), np.asarray(vs_r) + 9, where="mid",
            color=C_MISS, lw=1.5)
    ax.axvline(bstep, color=C_MARK, lw=2)
    ax.set_ylim(0, 9 + max(vs_r) + 4.5)
    ax.text(bstep + 4, 7.6, "front crosses\nA|B interface",
            color=C_MARK, fontsize=10)
    ax.text(4, 6.6, "crystal low region (A=10101, then B)",
            color=C_MATCH, fontsize=11)
    ax.text(4, 9 + max(vs_r) + 1.0, "random low region (offset +9)",
            color=C_MISS, fontsize=11)
    ax.set_xlabel("odd step")
    ax.set_ylabel("v (halvings per odd step)")
    ax.set_title("Q1: the LeastEdge rhythm, crystal vs random tail",
                 fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)

    # (2) autocorrelation peak distributions
    ax = axs[0][1]
    ac_c = [r[4] for r in q1 if r[0] == "crystal"]
    ac_r = [r[4] for r in q1 if r[0] == "random"]
    bins = np.linspace(0, 1.02, 40)
    ax.hist(ac_r, bins=bins, color=C_MISS, alpha=0.85)
    ax.hist(ac_c, bins=bins, color=C_MATCH, alpha=0.85)
    ax.text(0.03, 0.95, "random (n=%d)\nmean %.2f" % (len(ac_r),
            np.mean(ac_r)), color=C_MISS, transform=ax.transAxes, va="top",
            fontsize=11)
    ax.text(0.55, 0.95, "crystal (n=%d)\nmean %.2f\nCohen's d = %.1f" %
            (len(ac_c), np.mean(ac_c), cohens_d(ac_c, ac_r)), color=C_MATCH,
            transform=ax.transAxes, va="top", fontsize=11)
    ax.set_xlabel("max |autocorrelation| of v-sequence, lags 1..60")
    ax.set_ylabel("seeds")
    ax.set_title("Q1: rhythm order while the region is consumed", fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)

    # (3) changepoint accuracy
    ax = axs[0][2]
    db = [p["delay_bits"] for p in pairstats]
    hi = int(max(db))
    ax.hist(db, bins=np.arange(-0.5, hi + 1.5), color=C_MATCH)
    ax.set_yscale("log")
    med = np.median(db)
    ax.axvline(med, color=C_MARK, lw=2)
    ax.text(med + 0.3, ax.get_ylim()[1] * 0.4, "median +%d bit" % med,
            color=C_MARK, fontsize=11)
    ax.set_xlabel("bits consumed at rhythm divergence  -  interface position")
    ax.set_ylabel("pairs (log)")
    ax.set_title("Q2: the boundary is exact in the rhythm (n=%d pairs)"
                 % len(db), fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)

    # (4) wedge width at front arrival (L=5, same geometry as the wedge fig)
    ax = axs[1][0]
    wm = [p["wedge"] for p in pairstats
          if p["L"] == 5 and p["matched"] and p["wedge"] >= 0]
    wx = [p["wedge"] for p in pairstats
          if p["L"] == 5 and not p["matched"] and p["wedge"] >= 0]
    bins = np.arange(-0.5, DEF_HI + 2, 3)
    ax.hist(wx, bins=bins, color=C_MISS, alpha=0.85)
    ax.hist(wm, bins=bins, color=C_MATCH, alpha=0.85)
    ax.text(0.05, 0.9, "matched %.1f +- %.1f bits" % (np.mean(wm),
            np.std(wm)), color=C_MATCH, transform=ax.transAxes, fontsize=11)
    ax.text(0.05, 0.8, "mismatched %.1f +- %.1f bits" % (np.mean(wx),
            np.std(wx)), color=C_MISS, transform=ax.transAxes, fontsize=11)
    ax.text(0.05, 0.7, "d = %.2f: same wedge either way"
            % cohens_d(wx, wm), color=C_INK, transform=ax.transAxes,
            fontsize=11)
    ax.set_xlabel("wedge extent above interface when the front arrives (bits)")
    ax.set_ylabel("pairs")
    ax.set_title("Q3a: domain-wall wedge is charge-blind (L=5)", fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)

    # (5) relock delay (small-wedge geometry)
    ax = axs[1][1]
    for L, ls in ((5, "-"), (7, "--")):
        rm = [r["delay"] for r in relocks if r["L"] == L and r["matched"]
              and r["delay"] is not None]
        rx = [r["delay"] for r in relocks if r["L"] == L and not r["matched"]
              and r["delay"] is not None]
        bins = np.arange(0, 260, 10)
        hm, _ = np.histogram(rm, bins=bins, density=True)
        hx, _ = np.histogram(rx, bins=bins, density=True)
        mid = (bins[:-1] + bins[1:]) / 2
        ax.plot(mid, hm, color=C_MATCH, ls=ls, lw=2)
        ax.plot(mid, hx, color=C_MISS, ls=ls, lw=2)
        ax.text(0.55, 0.9 - 0.24 * (L == 7),
                "L=%d matched %.0f +- %.0f\nL=%d mismatched %.0f +- %.0f\n"
                "d = %.2f" % (L, np.mean(rm), np.std(rm), L, np.mean(rx),
                              np.std(rx), cohens_d(rx, rm)),
                color=C_INK, transform=ax.transAxes, fontsize=10, va="top")
    ax.set_xlabel("steps after the boundary until the rhythm re-locks")
    ax.set_ylabel("density (solid L=5, dashed L=7)")
    ax.set_title("Q3b: rhythm recovery does not depend on charge", fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)

    # (6) tiling consumption rate
    ax = axs[1][2]
    tm = [t["vbar"] for t in tilings if t["matched"] and not t["degenerate"]]
    tx = [t["vbar"] for t in tilings if not t["matched"]
          and not t["degenerate"]]
    bins = np.linspace(1.0, 2.8, 40)
    ax.hist(tx, bins=bins, color=C_MISS, alpha=0.85)
    ax.hist(tm, bins=bins, color=C_MATCH, alpha=0.85)
    ax.axvline(math.log2(3), color=C_INK, lw=1.2, ls="--")
    ax.text(math.log2(3) - 0.06, ax.get_ylim()[1] * 0.55, "log2(3)",
            color=C_INK, fontsize=10, rotation=90, va="center")
    ax.text(0.52, 0.9, "matched %.2f +- %.2f" % (np.mean(tm), np.std(tm)),
            color=C_MATCH, transform=ax.transAxes, fontsize=11)
    ax.text(0.52, 0.82, "mismatched %.2f +- %.2f" % (np.mean(tx),
            np.std(tx)), color=C_MISS, transform=ax.transAxes, fontsize=11)
    ax.text(0.52, 0.74, "d = %.2f (cycle census: flat)" % cohens_d(tx, tm),
            color=C_INK, transform=ax.transAxes, fontsize=11)
    ax.set_xlabel("mean v while consuming the (AB)^k tiling")
    ax.set_ylabel("pairs")
    ax.set_title("Q3c: even true compositions - no charge rate law",
                 fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("[real-CA rows] the bridge: composition atlas vs LeastEdge "
                 "rhythm - order is loud (Q1), boundaries are exact (Q2), "
                 "the x3 charge is silent in the rhythm (Q3: |d| <= 0.1 on "
                 "every rhythm observable)", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path = os.path.join(IMAGES, "collatz-bridge-stats.png")
    fig.savefig(path, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


# ----------------------------------------------------------------------- main

def main():
    verify()
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        return
    pool = Pool(16)

    print("\nQ1: crystal vs random low regions (%d-bit region)" % Q1_BITS)
    q1 = run_q1(pool)
    for kind in ("crystal", "random"):
        rows = [r for r in q1 if r[0] == kind]
        print("  %-8s n=%3d  mean v %.3f +- %.3f   acmax %.3f +- %.3f   "
              "periodic-in-window %d/%d"
              % (kind, len(rows), np.mean([r[3] for r in rows]),
                 np.std([r[3] for r in rows]), np.mean([r[4] for r in rows]),
                 np.std([r[4] for r in rows]),
                 sum(1 for r in rows if r[5] is not None), len(rows)))
    cr = [r for r in q1 if r[0] == "crystal"]
    rd = [r for r in q1 if r[0] == "random"]
    print("  crystal v-seq == 2-adic ideal of -A/(2^L-1): %d/%d exactly"
          % (sum(1 for r in cr if r[6]), len(cr)))
    print("  effect size (acmax): d = %.1f"
          % cohens_d([r[4] for r in cr], [r[4] for r in rd]))

    print("\nQ2/Q3a: domain pairs A^kA B^kB (L=5 exhaustive, L=7 sampled)")
    pairs = make_pairs()
    print("  running %d pairs..." % len(pairs))
    maps = {"m5": [None, None], "x5": [None, None]}
    pairstats, ideal_cache = [], {}
    ex_crystal = None
    for res in pool.imap_unordered(pair_worker, pairs, chunksize=16):
        st = analyze_pair(res, ideal_cache)
        if st is None:
            continue
        st.update(L=res["L"], A=res["A"], B=res["B"], matched=res["matched"],
                  wedge=res["wedge"])
        pairstats.append(st)
        if res["L"] == 5:
            key = "m5" if res["matched"] else "x5"
            dm = res["dm"]
            if maps[key][0] is None:
                maps[key][0] = np.zeros((TMAX_MAP, DEF_LO + DEF_HI))
                maps[key][1] = np.zeros((TMAX_MAP, DEF_LO + DEF_HI))
            maps[key][0][: len(dm)] += dm
            maps[key][1][: len(dm)] += 1
        if ex_crystal is None and res["L"] == 5 and res["A"] == 0b10101 \
                and res["matched"]:
            V = np.cumsum(res["vs"])
            bstep = int(np.searchsorted(V, res["boundary"]) + 1)
            ex_crystal = (res["vs"][:210], bstep)

    db = [p["delay_bits"] for p in pairstats]
    ds = [p["delay_steps"] for p in pairstats]
    blind = [p for p in pairstats if p["t_blind"] is not None]
    hit = [p for p in blind if abs(p["t_blind"] - p["t_div"]) <= 1]
    print("  Q2 changepoint: bits-consumed-at-divergence - interface: "
          "median %+d, IQR %d..%d, min %d, max %d"
          % (np.median(db), np.percentile(db, 25), np.percentile(db, 75),
             min(db), max(db)))
    print("     divergence step - predicted step: median %+d, IQR %d..%d"
          % (np.median(ds), np.percentile(ds, 25), np.percentile(ds, 75)))
    print("     blind changepoint within 1 step of true divergence: %d/%d"
          % (len(hit), len(blind)))
    nolock = sum(1 for p in pairstats if not p["relocked"])
    print("  Q3a: no relock within the 300-bit B region for %d/%d pairs "
          "(the wedge, not charge, controls recovery)"
          % (nolock, len(pairstats)))
    for L in (5, 7):
        gm = [p for p in pairstats if p["L"] == L and p["matched"]]
        gx = [p for p in pairstats if p["L"] == L and not p["matched"]]
        wm = [p["wedge"] for p in gm if p["wedge"] >= 0]
        wx = [p["wedge"] for p in gx if p["wedge"] >= 0]
        vm = [p["vbarB"] for p in gm if not math.isnan(p["vbarB"])]
        vx = [p["vbarB"] for p in gx if not math.isnan(p["vbarB"])]
        print("  L=%d wedge at arrival: matched %5.1f +- %3.1f vs mismatched "
              "%5.1f +- %3.1f bits (d = %+.2f);  B-phase vbar %.3f vs %.3f "
              "(d = %+.2f)" % (L, np.mean(wm), np.std(wm), np.mean(wx),
                               np.std(wx), cohens_d(wx, wm), np.mean(vm),
                               np.mean(vx), cohens_d(vx, vm)))

    print("\nQ3b: relock experiment (small wedge: kA=%d/%d)"
          % (RELOCK_CFG[5]["kA"], RELOCK_CFG[7]["kA"]))
    rjobs = [(L, A, B) for (L, A, B) in pairs]
    relocks = pool.map(relock_worker, rjobs, chunksize=16)
    for L in (5, 7):
        rm = [r for r in relocks if r["L"] == L and r["matched"]]
        rx = [r for r in relocks if r["L"] == L and not r["matched"]]
        dm = [r["delay"] for r in rm if r["delay"] is not None]
        dx = [r["delay"] for r in rx if r["delay"] is not None]
        print("  L=%d relocked %d/%d matched, %d/%d mismatched;  delay "
              "%5.1f +- %4.1f vs %5.1f +- %4.1f steps  (d = %+.2f)"
              % (L, len(dm), len(rm), len(dx), len(rx), np.mean(dm),
                 np.std(dm), np.mean(dx), np.std(dx), cohens_d(dx, dm)))

    print("\nQ3c: tiling (AB)^k - the true-composition geometry")
    tjobs = [(5, A, B) for A in range(1, 32, 2) for B in range(1, 32)
             if B != A]
    tilings = pool.map(tiling_worker, tjobs, chunksize=16)
    tm = [t["vbar"] for t in tilings if t["matched"] and not t["degenerate"]]
    tx = [t["vbar"] for t in tilings if not t["matched"]
          and not t["degenerate"]]
    dg = [t for t in tilings if t["degenerate"]]
    print("  vbar: matched %.3f +- %.3f (n=%d) vs mismatched %.3f +- %.3f "
          "(n=%d), d = %+.2f" % (np.mean(tm), np.std(tm), len(tm),
                                 np.mean(tx), np.std(tx), len(tx),
                                 cohens_d(tx, tm)))
    for t in dg:
        print("  degenerate X=%d = (2^10-1)/3: tail = -1/3, the whole region "
              "annihilates in one step (A=%d B=%d)" % (t["X"], t["A"], t["B"]))

    print("\ncycle census [value]: eventual-cycle vbar of ALL width-p "
          "crystals, by v3(X)")
    census = run_census(pool)
    for p in (5, 7, 9, 10, 12, 14):
        rows = [r for r in census if r[0] == p]
        line = "  p=%2d (quota 3^%d): " % (p, v3((1 << p) - 1))
        for e in (0, 1, 2):
            g = [r for r in rows if min(v3(r[1]), 2) == e]
            if g:
                line += " v3=%d%s: vbar %.3f (n=%d) " % (
                    e, "+" if e == 2 else "", np.mean([r[4] for r in g]),
                    len(g))
        neg = [r for r in rows if r[5]]
        line += "  negative cycles: %d" % len(neg)
        print(line)
    pool.close()
    pool.join()

    rng = random.Random(99)
    vs_r = vseq((1 << Q1_BITS) | rng.getrandbits(Q1_BITS) | 1,
                Q1_BITS - Q1_MARGIN)[:210]
    fig_hex()
    fig_wedge({k: tuple(v) for k, v in maps.items()})
    fig_stats(q1, pairstats, relocks, tilings, (ex_crystal, vs_r))


if __name__ == "__main__":
    main()
