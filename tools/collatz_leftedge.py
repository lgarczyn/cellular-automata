#!/usr/bin/env python3
"""The left edge: noise vs pattern PAST the starting MSB. SCOPE: [real-CA].

The right edge is programmed 2-adically (low digits: blocks, runners,
splices). This module asks Lou's left-edge question: does anything ever
appear in the fresh territory - tape cells strictly LEFT of the seed's own
leftmost column - other than noise?  And with what quantifier do you tell?

Physics of that region: cells above the seed's MSB are written by the pure
x3 flow (the +1 carries reach only ~log2(3)*T low bits), so row T of the
fresh region is the leading-bit field of 3^T * n. That is the ARCHIMEDEAN
(real-mantissa) side of the machine, the mirror of the 2-adic right side.

Quantifier (calibrated on random seeds of the same size, z-scores):
  z_c   compression gain: zlib(region) vs the same bits shuffled within
        their rows (kills order, keeps every row's density)
  z_p   periodicity: mean over rows of the max normalized autocorrelation
  z_r   constant-run excess: longest run of identical bits per row
A seed is "structured" when any z > 5 (random seeds sit at |z| < ~3).

The laws this file verifies:
  LAW 1 (exact): above LeastEdge + 40 cells the tape is bit-for-bit the pure
  x3 flow (0 mismatches; the highest +1-carry ripple ever observed reaches
  18 cells above the sea).  Near the sea the region is the affine flow
  3^r*n + C_r; at small tape thickness the correction C_r can complete or
  break a marginal aim (polarity tipping: 0111... -> 1000...).
  LAW 2: with adequate thickness the quantifier scores of the real region
  and the synthetic pure-x3 region agree (96-bit check: max |dz| = 1.6);
  the CA adds no structure of its own and destroys none.
  STRUCTURE = AIMING: the only structured seeds are n ~ P * 2^g / 3^k
  (low-complexity P): the pattern P materializes at step k in a constant
  field, then runs its own x3 river.  The set is measure-zero and gradient-
  free: hill climbing plateaus at z ~ 4 while designed aims reach z ~ 19
  (unbounded with size).

Search (this file runs all of it):
  - the null field: random seeds, the fuse, every zoo block, 3-smooth seeds
  - exhaustive scan of every odd 18-bit seed
  - hill-climbing on 96-bit seeds, maximizing the quantifier
  - designed families: n ~ P * 2^g / 3^k (ternary-mantissa aiming)
"""
import random
import sys
import zlib
from math import log2

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__file__))
import collatz_compose as C

LOG23 = log2(3)


def fresh_region(n, T):
    """Rows of tape bits at absolute positions >= b0 (past the seed's MSB).
    Returns (b0, rows) with rows = list of (start_offset, np.uint8 bits),
    start_offset = first valid column - b0 (nonzero once the sea passes b0).
    """
    b0 = n.bit_length()
    x, S, rows = n, 0, []
    for _ in range(T):
        if x <= 1:
            break
        m = 3 * x + 1
        v = (m & -m).bit_length() - 1
        x = m >> v
        S += v
        top = S + x.bit_length()
        start = max(b0, S)
        if top <= start:
            rows.append((0, np.zeros(0, np.uint8)))
            continue
        seg = (x >> (start - S)) & ((1 << (top - start)) - 1)
        bits = np.frombuffer(
            seg.to_bytes((top - start + 7) // 8, "little"), np.uint8)
        bits = np.unpackbits(bits, bitorder="little")[: top - start]
        rows.append((start - b0, bits))
    return b0, rows


def row_autocorr(bits, maxlag=48):
    x = bits.astype(np.float64)
    x -= x.mean()
    d = np.dot(x, x)
    if d < 1e-9:
        return 1.0                       # constant row = perfectly ordered
    best = 0.0
    for lag in range(2, min(maxlag, len(x) // 2) + 1):
        c = np.dot(x[:-lag], x[lag:]) / d
        best = max(best, c)
    return best


def longest_const_run(bits):
    """Longest run of IDENTICAL bits (zeros or ones - an aim from below 2^g
    gives ones in the pure flow, and the +1 carries tip it into zeros)."""
    if len(bits) == 0:
        return 0
    best = cur = 1
    for i in range(1, len(bits)):
        cur = cur + 1 if bits[i] == bits[i - 1] else 1
        best = max(best, cur)
    return best


def features(rows, rng=None, skip=3):
    """(zlib_gain, mean_autocorr, zero_run_fraction) of the fresh region."""
    use = [b for _, b in rows[skip:] if len(b) >= 16]
    if not use:
        return None
    flat = np.concatenate(use)
    c_real = len(zlib.compress(np.packbits(flat).tobytes(), 6))
    rs = np.random.RandomState(12345)
    shufs = []
    for _ in range(4):
        parts = []
        for b in use:
            p = b.copy()
            rs.shuffle(p)
            parts.append(p)
        shufs.append(len(zlib.compress(
            np.packbits(np.concatenate(parts)).tobytes(), 6)))
    gain = 1.0 - c_real / (sum(shufs) / len(shufs))
    ac = float(np.mean([row_autocorr(b) for b in use]))
    zr = float(np.mean([longest_const_run(b) / len(b) for b in use]))
    return gain, ac, zr


def run_features(n, T):
    _, rows = fresh_region(n, T)
    return features(rows)


class Baseline:
    def __init__(self, bitlen, T, N=120, seed=7):
        rng = random.Random(seed)
        vals = []
        while len(vals) < N:
            n = rng.getrandbits(bitlen - 2) | (1 << (bitlen - 1)) | 1
            f = run_features(n, T)
            if f:
                vals.append(f)
        a = np.array(vals)
        self.mu = a.mean(axis=0)
        # floor the spread: random-seed zlib gain is ~constant (sd ~ 0), and
        # a z-score against a zero sd is meaningless
        self.sd = np.maximum(a.std(axis=0), (0.01, 0.02, 0.02))

    def z(self, f):
        if f is None:
            return None
        return tuple((np.array(f) - self.mu) / self.sd)


def zmax(zs):
    return max(zs) if zs else float("-inf")


# ------------------------------------------------------------ the families

def family_seeds(bitlen=96):
    """Named 96-bit seeds for the null-field and designed families."""
    rng = random.Random(99)
    out = []
    for i in range(3):
        out.append(("random-%d" % i,
                    rng.getrandbits(bitlen - 2) | (1 << (bitlen - 1)) | 1))
    out.append(("fuse 2^96-1", (1 << bitlen) - 1))
    blocks = C.enumerate_blocks(6)
    for den in (11, 49, 31, 217):
        b = next(x for x in blocks if x.den == den)
        M = bitlen - (bitlen % b.q)
        out.append(("block d%d words" % den, C.expansion(b.x, M) | (1 << (M - 1))))
    # 3-smooth: pure ternary river
    k = int(bitlen / LOG23)
    out.append(("3^%d (3-smooth)" % k, 3**k))
    # sparse: shifted copies of the same river + void wedges
    out.append(("sparse 2^95+2^55+1", (1 << 95) | (1 << 55) | 1))
    # ternary aiming: n ~ 2^g/3^k -> left edge crystallizes at step k
    for k in (12, 20):
        g = int(round(bitlen + k * LOG23))
        out.append(("2^%d/3^%d (aimed)" % (g, k), (2**g // 3**k) | 1))
    # pattern materializer: P appears at step k
    P = int("10" * 24, 2)
    k = 16
    g = int(round(k * LOG23)) + 1
    out.append(("(1010..)*2^%d/3^%d" % (g, k), (P * 2**g // 3**k) | 1))
    return out


def sweep_families(T=44, bitlen=96):
    base = Baseline(bitlen, T)
    print("=== null field + families, %d-bit seeds, T=%d ===" % (bitlen, T))
    print("%-26s %8s %8s %8s   %s" % ("seed", "z_zlib", "z_acorr", "z_zrun",
                                      "verdict"))
    results = []
    for name, n in family_seeds(bitlen):
        f = run_features(n, T)
        zs = base.z(f)
        v = "STRUCTURE" if zs and zmax(zs) > 5 else "noise"
        print("%-26s %8.1f %8.1f %8.1f   %s"
              % (name, zs[0], zs[1], zs[2], v))
        results.append((name, n, zs))
    return base, results


# ------------------------------------------------------- exhaustive 18-bit

def scan_18bit(T=22):
    bitlen = 18
    base = Baseline(bitlen, T, N=150)
    print("\n=== exhaustive scan: every odd 18-bit seed, T=%d ===" % T)
    top = []
    for n in range((1 << 17) + 1, 1 << 18, 2):
        f = run_features(n, T)
        zs = base.z(f)
        if zs is None:
            continue
        s = zmax(zs)
        top.append((s, n, zs))
    top.sort(reverse=True)
    n_struct = sum(1 for s, _, _ in top if s > 5)
    print("seeds with z > 5: %d / %d" % (n_struct, len(top)))
    print("%-8s %-10s %6s %6s %6s  %-9s %s" %
          ("n", "hex", "z_c", "z_a", "z_r", "popcount", "3-aim (k, err)"))
    for s, n, zs in top[:25]:
        k, err = ternary_aim(n)
        print("%-8d %-10s %6.1f %6.1f %6.1f  %-9d k=%-3d %.4f"
              % (n, hex(n), zs[0], zs[1], zs[2], bin(n).count("1"), k, err))
    return top


def ternary_aim(n, kmax=40):
    """How close is n to some 2^g/3^k?  err = distance of log2(n*3^k) from
    an integer (0 = exact aiming)."""
    best = (0, 0.5)
    l2 = log2(n)
    for k in range(kmax + 1):
        fr = (l2 + k * LOG23) % 1.0
        err = min(fr, 1.0 - fr)
        if err < best[1]:
            best = (k, err)
    return best


def aim_general(n, T, pbits=6, top_w=24):
    """General P-aiming: the longest constant run right after a short prefix
    P in the leading bits of n * 3^k, over k <= T.  A long run means
    n ~ P * 2^g / 3^k: the pattern P materializes at step k inside a
    constant field.  Returns (run, k, P)."""
    best = (0, 0, 0)
    m = n
    for k in range(1, T + 1):
        m *= 3
        bl = m.bit_length()
        s = bin(m >> max(0, bl - top_w))[2:]
        for j in range(1, min(pbits, len(s) - 1) + 1):
            ch = s[j]
            run = 0
            for c in s[j:]:
                if c != ch:
                    break
                run += 1
            if run > best[0]:
                best = (run, k, int(s[:j], 2))
    return best


def aim_err_general(n, T, Pmax=63):
    """min over k <= T, odd P <= Pmax of the log2-distance from n*3^k to the
    nearest P*2^g.  Small err = the left edge will display P at step k."""
    l2 = log2(n)
    targets = [(log2(P) % 1.0, P) for P in range(1, Pmax + 1, 2)]
    best = (1.0, 0, 1)
    for k in range(1, T + 1):
        fr = (l2 + k * LOG23) % 1.0
        for tp, P in targets:
            d = abs(fr - tp)
            d = min(d, 1.0 - d)
            if d < best[0]:
                best = (d, k, P)
    return best


def law1_physics(nseeds=300, bitlen=48, T=30, margin=40, seed=3):
    """LAW 1 (exact): the +1 of each step injects at the CURRENT LeastEdge,
    so its carries live near the sea.  Above S_{r-1} + margin the tape is
    bit-for-bit the pure x3 flow: cell at absolute position p in row r
    equals bit p of 3^r * n.  Also measures the highest carry ripple ever
    seen above the sea (margin=2 pass)."""
    rng = random.Random(seed)
    bad = tot = 0
    max_ripple = 0
    for _ in range(nseeds):
        n = rng.getrandbits(bitlen - 2) | (1 << (bitlen - 1)) | 1
        b0 = n.bit_length()
        x, S = n, 0
        m3 = n
        for r in range(1, T + 1):
            if x <= 1:
                break
            Sprev = S
            mm = 3 * x + 1
            v = (mm & -mm).bit_length() - 1
            x = mm >> v
            S += v
            m3 *= 3
            hi = S + x.bit_length()
            # strict check above the margin
            lo = max(b0, S, Sprev + margin)
            if hi > lo:
                seg_ca = (x >> (lo - S)) & ((1 << (hi - lo)) - 1)
                seg_x3 = (m3 >> lo) & ((1 << (hi - lo)) - 1)
                tot += hi - lo
                bad += bin(seg_ca ^ seg_x3).count("1")
            # ripple measurement from just above the sea
            lo2 = max(b0, S, Sprev + 2)
            if hi > lo2:
                d = ((x >> (lo2 - S)) ^ (m3 >> lo2)) & ((1 << (hi - lo2)) - 1)
                if d:
                    max_ripple = max(max_ripple,
                                     d.bit_length() + lo2 - Sprev)
    print("\n=== LAW 1 (physics): fresh region = pure x3 flow ===")
    print("%d seeds x %d rows: %d cells checked above LeastEdge+%d: "
          "%d mismatches; highest carry ripple ever seen: %d cells "
          "above the LeastEdge" % (nseeds, T, tot, margin, bad, max_ripple))
    return bad, max_ripple


def synth_region(n, T):
    """The pure x3 prediction of the fresh region: bits of 3^r * n at the
    same absolute positions the real run exposes."""
    b0 = n.bit_length()
    x, S, m3, rows = n, 0, n, []
    for _ in range(T):
        if x <= 1:
            break
        mm = 3 * x + 1
        v = (mm & -mm).bit_length() - 1
        x = mm >> v
        S += v
        m3 *= 3
        top = S + x.bit_length()
        start = max(b0, S)
        if top <= start:
            rows.append((0, np.zeros(0, np.uint8)))
            continue
        seg = (m3 >> start) & ((1 << (top - start)) - 1)
        bits = np.frombuffer(
            seg.to_bytes((top - start + 7) // 8, "little"), np.uint8)
        bits = np.unpackbits(bits, bitorder="little")[: top - start]
        rows.append((start - b0, bits))
    return b0, rows


def law2_no_ca_magic(top, T=22, zthr=5.0, seed=11):
    """LAW 2: every structured region is EXPLAINED by the x3 mantissa flow:
    the same quantifier on the synthetic pure-x3 region gives the same
    z-scores.  If the CA added structure of its own, z_real >> z_syn
    somewhere; if it destroyed it, z_real << z_syn."""
    base = Baseline(18, T, N=150)
    struct = [(s, n) for s, n, _ in top if s > zthr]
    rng = random.Random(seed)
    rand = [rng.getrandbits(16) | (1 << 17) | 1 for _ in range(150)]
    diffs = []
    for n in [n for _, n in struct] + rand:
        zr = base.z(features(fresh_region(n, T)[1]))
        zs = base.z(features(synth_region(n, T)[1]))
        if zr is None or zs is None:
            continue
        diffs.append((max(abs(a - b) for a, b in zip(zr, zs)),
                      zmax(zr), zmax(zs), n))
    diffs.sort(reverse=True)
    worst = diffs[0]
    agree = sum(1 for d, _, _, _ in diffs if d < 1.0)
    print("\n=== LAW 2 (no CA magic): real region vs pure-x3 synthetic ===")
    print("%d seeds (all structured + 150 random): max |z_real - z_syn| "
          "< 1 for %d (%.1f%%); worst |dz|=%.2f (z_real=%.1f z_syn=%.1f "
          "n=%d)" % (len(diffs), agree, 100.0 * agree / len(diffs), *worst))
    return diffs


def law2_structure(top, T=22, zthr=5.0, nrand=600, seed=11):
    """LAW 2 (statistics): structured seeds are the P-aimed seeds.  Compare
    the generalized aim error of the z>thr set vs random seeds."""
    rng = random.Random(seed)
    r_errs = sorted(aim_err_general(
        rng.getrandbits(16) | (1 << 17) | 1, T)[0] for _ in range(nrand))
    s_list = [(aim_err_general(n, T), s, n) for s, n, _ in top if s > zthr]
    s_errs = sorted(e for (e, _, _), _, _ in s_list)
    med = lambda a: a[len(a) // 2]
    r_med, s_med = med(r_errs), med(s_errs)
    r_q10 = r_errs[len(r_errs) // 10]
    frac_below = sum(1 for e in s_errs if e < r_q10) / len(s_errs)
    print("\n=== LAW 2 (structure = aiming): aim err distributions ===")
    print("random median aim err: %.2e (10th pct %.2e)" % (r_med, r_q10))
    print("structured (z>%.0f) median aim err: %.2e  (%.0fx smaller); "
          "%.0f%% sit below the random 10th percentile"
          % (zthr, s_med, r_med / s_med, 100 * frac_below))
    print("examples: " + "  ".join(
        "n=%d->P=%d@k=%d" % (n, P, k)
        for (e, k, P), s, n in sorted(s_list)[:6]))
    return s_list


# ------------------------------------------------------------- hill climb

def hillclimb(base, T=44, bitlen=96, restarts=24, iters=320, seed=5):
    print("\n=== hill climb: %d-bit seeds, %d restarts x %d flips, "
          "maximizing max-z ===" % (bitlen, restarts, iters))
    rng = random.Random(seed)
    champs = []
    for r in range(restarts):
        n = rng.getrandbits(bitlen - 2) | (1 << (bitlen - 1)) | 1
        zs = base.z(run_features(n, T))
        s = zmax(zs)
        for _ in range(iters):
            m = n
            for _ in range(rng.choice((1, 1, 2, 3))):
                m ^= 1 << rng.randrange(1, bitlen - 1)
            m |= (1 << (bitlen - 1)) | 1
            z2 = base.z(run_features(m, T))
            s2 = zmax(z2)
            if s2 >= s:
                n, s, zs = m, s2, z2
        champs.append((s, n, zs))
    champs.sort(reverse=True)
    for s, n, zs in champs[:8]:
        k, err = ternary_aim(n)
        print("z=%6.1f  n=%s  popcount=%d  3-aim k=%d err=%.4f"
              % (s, hex(n), bin(n).count("1"), k, err))
    return champs


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "families"):
        base, fam = sweep_families()
    if which in ("all", "laws", "scan"):
        law1_physics()
        top = scan_18bit()
        law2_no_ca_magic(top)
        law2_structure(top)
    if which in ("all", "climb"):
        if which == "climb":
            base = Baseline(96, 44)
        hillclimb(base)


if __name__ == "__main__":
    main()
