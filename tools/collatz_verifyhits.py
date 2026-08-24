#!/usr/bin/env python3
"""Stage 2 for the C leftscan: mechanism-verify every hit. SCOPE: [real-CA].

For each hit from the exhaustive 32-bit / random 64-bit C scan, recompute
structure on the real region and on the synthetic pure-x3 region (exact
bignum), and classify: mantissa-explained / affine-tipped / broken /
UNEXPLAINED. Vertical-channel hits (per-seed quasicrystal anomaly) are
checked against the +1-carry explanation: at these sizes the front window
includes carry-affected bits, so anomalies must vanish on the synthetic
flow; any that survive would be new physics.
"""
import glob
import sys
from math import log2

sys.path.insert(0, __import__("os").path.dirname(__file__))
import collatz_bigscan as B
import collatz_river as RV

LOG23 = log2(3)


def vert_anomaly(M, pred_cache={}):
    best = -100.0
    T = len(M)
    for m in range(2, T - 8):
        if m not in pred_cache:
            pred_cache[m] = RV.predicted_depth(m)
        depths = []
        for r in range(T - m):
            a, b = M[r], M[m + r]
            neq = a != b
            depths.append(neq.argmax() if neq.any() else len(a))
        if len(depths) >= 8:
            best = max(best, sum(depths) / len(depths) - pred_cache[m])
    return best


def synth_front(n, T, W=32):
    rows = []
    x, m3 = n, n
    for _ in range(T):
        if x <= 1:
            break
        mm = 3 * x + 1
        x = mm >> ((mm & -mm).bit_length() - 1)
        m3 *= 3
        bl = m3.bit_length()
        if bl >= W and x.bit_length() >= W:
            top = m3 >> (bl - W)
            rows.append([(top >> (W - 1 - i)) & 1 for i in range(W)])
    import numpy as np
    return np.array(rows, dtype=np.uint8)


def main():
    pattern = sys.argv[1] if len(sys.argv) > 1 else \
        "/var/tmp/collatz-scratch/leftscan/exh32_*.txt"
    T = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    hits = []
    for path in glob.glob(pattern):
        for line in open(path):
            p = line.split()
            hits.append((int(p[0]),) + tuple(map(float, p[1:])))
    print("%d hits from %s" % (len(hits), pattern))
    if not hits:
        return
    mantissa = tipped = broken = 0
    unex = []
    vhits = [h for h in hits if h[4] > 5.0]
    rowhits = [h for h in hits if max(h[1], h[2], h[3]) > 0 and h not in vhits]
    # row-channel hits: real vs synthetic cheap scores
    for h in sorted(rowhits, key=lambda h: -max(h[1:4]))[:20000]:
        n = h[0]
        mt, mf, _ = B.cheap(n, T)
        st, sf = B.cheap_synth(n, T)
        if abs(mt - st) < 0.1 and abs(mf - sf) < 0.1:
            mantissa += 1
        elif max(mt - st, mf - sf) > 0:
            tipped += 1
        else:
            broken += 1
    print("row-channel hits: %d mantissa-explained, %d affine-tipped, "
          "%d broken" % (mantissa, tipped, broken))
    # vertical-channel hits: anomaly must vanish (or persist!) on synthetic
    import numpy as np

    def real_front(n, T, W=32):
        # skip thin rows (like the C scanner) instead of breaking
        rows = []
        x = n
        for _ in range(T):
            if x <= 1:
                break
            mm = 3 * x + 1
            x = mm >> ((mm & -mm).bit_length() - 1)
            b = x.bit_length()
            if b >= W:
                top = x >> (b - W)
                rows.append([(top >> (W - 1 - i)) & 1 for i in range(W)])
        return np.array(rows, dtype=np.uint8)

    def is_flashy(M):
        # a flash/aim zone: some row with a >=24-bit constant run
        for row in M:
            first = row[1]
            c = 0
            for v in row[1:]:
                if v != first:
                    break
                c += 1
            if c >= 24:
                return True
        return False

    agree = flashy = new = 0
    for h in sorted(vhits, key=lambda h: -h[4])[:400]:
        n = h[0]
        Mr = real_front(n, T, 32)
        Ms = synth_front(n, T, 32)
        ar = vert_anomaly(Mr) if len(Mr) > 12 else -100
        as_ = vert_anomaly(Ms) if len(Ms) > 12 else -100
        if is_flashy(Mr) or is_flashy(Ms):
            flashy += 1
        elif abs(ar - as_) < 1.5:
            agree += 1
        else:
            new += 1
            if new <= 8:
                print("   NEW? n=%d real=%.2f synth=%.2f" % (n, ar, as_))
    print("vertical-channel hits: %d checked: %d are flash/aim zones, "
          "%d real==synth (mantissa), %d unexplained"
          % (min(len(vhits), 400), flashy, agree, new))


if __name__ == "__main__":
    main()
