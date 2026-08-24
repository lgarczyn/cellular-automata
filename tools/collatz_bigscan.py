#!/usr/bin/env python3
"""The big left-edge scan: multi-scale, multi-frame, 16 cores.
SCOPE: [real-CA]. Stage 1: cheap per-row features (constant runs and exact
short periods, in BOTH the tape frame past the start column and the
MSB-aligned front window) over millions of seeds. Stage 2: survivors get
the full quantifier plus aim classification (raw P-aim, affine aim); what
remains unexplained is dumped for inspection.

Configs: exhaustive odd 23-bit; random 48/96/256/700-bit.
"""
import os
import random
import sys
from math import log2
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LOG23 = log2(3)
OUT = "/var/tmp/collatz-scratch/bigscan"


def run1(x):
    c = 0
    while x:
        x &= x >> 1
        c += 1
    return c


def rowscore(seg, w):
    """max(constant-run fraction, best exact short-period match) of an
    integer segment of width w."""
    if w < 12:
        return 0.0
    mask = (1 << w) - 1
    seg &= mask
    r1 = run1(seg)
    r0 = run1(~seg & mask)
    best = max(r1, r0) / w
    for p in (2, 3, 4, 5, 6, 7, 8):
        d = (seg ^ (seg >> p)) & ((1 << (w - p)) - 1)
        m = 1.0 - bin(d).count("1") / (w - p)
        if m > best:
            best = m
    return best


def cheap(n, T):
    """(max tape-frame rowscore, max front rowscore, mean tape rowscore)."""
    b0 = n.bit_length()
    ts, fs = [], []
    x, S = n, 0
    for _ in range(T):
        if x <= 1:
            break
        m = 3 * x + 1
        v = (m & -m).bit_length() - 1
        x = m >> v
        S += v
        top = S + x.bit_length()
        start = max(b0, S)
        w = top - start
        if w >= 14:
            ts.append(rowscore(x >> (start - S), w))
        bl = x.bit_length()
        if bl >= 26:
            fs.append(rowscore(x >> (bl - 26), 26))
    ts.sort(reverse=True)
    fs.sort(reverse=True)
    top3 = lambda a: sum(a[:3]) / 3 if len(a) >= 3 else 0.0
    return top3(ts), top3(fs), (sum(ts) / len(ts) if ts else 0.0)


def work_exh(args):
    lo, hi, T, thr_t, thr_f = args
    hits = []
    for n in range(lo | 1, hi, 2):
        mt, mf, mean_t = cheap(n, T)
        if mt > thr_t or mf > thr_f:
            hits.append((n, mt, mf, mean_t))
    return hits


def work_rand(args):
    seed, count, bits, T, thr_t, thr_f = args
    rng = random.Random(seed)
    hits = []
    for _ in range(count):
        n = rng.getrandbits(bits - 2) | (1 << (bits - 1)) | 1
        mt, mf, mean_t = cheap(n, T)
        if mt > thr_t or mf > thr_f:
            hits.append((n, mt, mf, mean_t))
    return hits


def calibrate(bits, T, N=3000, seed=1):
    rng = random.Random(seed)
    ts, fs = [], []
    for _ in range(N):
        n = rng.getrandbits(bits - 2) | (1 << (bits - 1)) | 1
        mt, mf, _ = cheap(n, T)
        ts.append(mt)
        fs.append(mf)
    ts.sort()
    fs.sort()
    q = int(N * 0.999)
    return ts[q], fs[q], ts[-1], fs[-1]


def aim_err(n, T, Pmax=1023):
    l2 = log2(n)
    targets = [(log2(P) % 1.0) for P in range(1, Pmax + 1, 2)]
    best = 1.0
    for k in range(1, T + 1):
        fr = (l2 + k * LOG23) % 1.0
        for tp in targets:
            d = abs(fr - tp)
            d = min(d, 1.0 - d)
            if d < best:
                best = d
    return best


def scan_exhaustive(bits=23, T=30, procs=14):
    thr_t, thr_f, mx_t, mx_f = calibrate(bits, T)
    print("[exh %d-bit] thresholds 99.9%%: tape %.3f front %.3f "
          "(random max %.3f / %.3f)" % (bits, thr_t, thr_f, mx_t, mx_f))
    lo, hi = 1 << (bits - 1), 1 << bits
    step = (hi - lo) // (procs * 8)
    jobs = [(a, min(a + step, hi), T, mx_t, mx_f)
            for a in range(lo, hi, step)]
    hits = []
    with Pool(procs) as p:
        for h in p.imap_unordered(work_exh, jobs):
            hits.extend(h)
    total = (hi - lo) // 2
    print("[exh %d-bit] %d candidates above RANDOM MAX out of %d seeds"
          % (bits, len(hits), total))
    return hits, T


def scan_random(bits, T, total, procs=14):
    thr_t, thr_f, mx_t, mx_f = calibrate(bits, T,
                                         N=2000 if bits <= 256 else 600)
    print("[rand %d-bit] thresholds 99.9%%: tape %.3f front %.3f "
          "(random max %.3f / %.3f)" % (bits, thr_t, thr_f, mx_t, mx_f))
    per = total // procs
    jobs = [(1000 + i, per, bits, T, mx_t, mx_f) for i in range(procs)]
    hits = []
    with Pool(procs) as p:
        for h in p.imap_unordered(work_rand, jobs):
            hits.extend(h)
    print("[rand %d-bit] %d candidates above RANDOM MAX out of %d seeds"
          % (bits, len(hits), per * procs))
    return hits, T


def cheap_synth(n, T):
    """Same cheap features on the PURE x3 flow (bits of 3^r * n at the same
    positions): the mantissa-mechanism prediction for the region."""
    b0 = n.bit_length()
    ts, fs = [], []
    x, S, m3 = n, 0, n
    for _ in range(T):
        if x <= 1:
            break
        m = 3 * x + 1
        v = (m & -m).bit_length() - 1
        x = m >> v
        S += v
        m3 *= 3
        top = S + x.bit_length()
        start = max(b0, S)
        w = top - start
        if w >= 14:
            ts.append(rowscore(m3 >> start, w))
        bl = m3.bit_length()
        if bl >= 26:
            fs.append(rowscore(m3 >> (bl - 26), 26))
    ts.sort(reverse=True)
    fs.sort(reverse=True)
    top3 = lambda a: sum(a[:3]) / 3 if len(a) >= 3 else 0.0
    return top3(ts), top3(fs)


def classify(hits, T, tag, tol=0.08):
    """Stage 2: mechanism verification. For every hit, does the pure-x3
    mantissa flow reproduce the structure scores?  'mantissa' = yes;
    'tipped' = real > synthetic (the +1 correction completed a marginal
    aim - the affine flow, same mechanism at one remove); 'lost' = real
    < synthetic (the +1s broke a pure-flow aim).  A hit outside all three
    would be genuinely new physics; by LAW 1 none can exist above the
    carry horizon, so this doubles as a pipeline check."""
    mantissa, tipped, lost = [], [], []
    for n, mt, mf, mean_t in sorted(hits, key=lambda h: -max(h[1], h[2])):
        st, sf = cheap_synth(n, T)
        d_t, d_f = mt - st, mf - sf
        rec = (n, mt, mf, st, sf, aim_err(n, T))
        if abs(d_t) < tol and abs(d_f) < tol:
            mantissa.append(rec)
        elif max(d_t, d_f) > 0:
            tipped.append(rec)
        else:
            lost.append(rec)
    print("[%s] %d hits: %d mantissa-explained, %d affine-tipped, "
          "%d flow-structure broken by the +1s"
          % (tag, len(hits), len(mantissa), len(tipped), len(lost)))
    for name, group in (("tipped", tipped), ("lost", lost)):
        for n, mt, mf, st, sf, e in group[:4]:
            print("   %s n=%d real(t=%.2f,f=%.2f) synth(t=%.2f,f=%.2f) "
                  "aimerr=%.5f" % (name, n, mt, mf, st, sf, e))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "%s_hits.txt" % tag), "w") as f:
        for n, mt, mf, st, sf, e in mantissa + tipped + lost:
            f.write("%d %.4f %.4f %.4f %.4f %.5f\n"
                    % (n, mt, mf, st, sf, e))
    return mantissa, tipped, lost


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "exh"
    if which == "exh":
        hits, T = scan_exhaustive(23, 30)
        classify(hits, T, "exh23")
    elif which == "r48":
        hits, T = scan_random(48, 60, 400000)
        classify(hits, T, "r48")
    elif which == "r96":
        hits, T = scan_random(96, 90, 150000)
        classify(hits, T, "r96")
    elif which == "r256":
        hits, T = scan_random(256, 200, 30000)
        classify(hits, T, "r256")
    elif which == "r700":
        hits, T = scan_random(700, 500, 5000)
        classify(hits, T, "r700")


if __name__ == "__main__":
    main()
