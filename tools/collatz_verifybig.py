#!/usr/bin/env python3
"""Stage 2 for the big-tape scan (1024/4096/16384-bit seeds).
SCOPE: [real-CA]. Mechanism verification of every hit: recompute the four
channels on the real run and on the pure-x3 flow, exact bignum.

Channels (matching tools/leftscan/bigtape.c):
  f front-64 rows, t base-window rows (absolute [b0, b0+64)),
  c base-window time-columns, v front vertical anomaly.
Verdicts per hit: 'mantissa' (pure flow reproduces the scores),
'tipped' (real > flow), 'lost' (real < flow), plus the aim location.
"""
import glob
import math
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))

LOG23 = math.log2(3)
LOG2W = math.log2(64.0)


def runlen(t):
    c = 0
    while t:
        t &= t >> 1
        c += 1
    return c


def rowscore64(seg):
    seg &= (1 << 64) - 1
    best = max(runlen(seg), runlen(~seg & ((1 << 64) - 1)))
    for p in range(2, 9):
        mm = (1 << (64 - p)) - 1
        d = (seg ^ (seg >> p)) & mm
        z = runlen(~d & mm)
        best = max(best, z)
    return best - LOG2W


def top3avg(a):
    a = sorted(a, reverse=True)
    return sum(a[:3]) / 3 if len(a) >= 3 else 0.0


def channels(n, T, pure=False):
    """(f, t, c) channels + the row index and value of the strongest front
    row (the flash location)."""
    b0 = n.bit_length()
    x, S, m3 = n, 0, n
    fs, ts = [], []
    cols = {}
    best = (-1e9, None, None)
    trow = 0
    for r in range(1, T + 1):
        mm = 3 * x + 1
        v = (mm & -mm).bit_length() - 1
        x = mm >> v
        S += v
        m3 *= 3
        val = m3 if pure else x
        blv = val.bit_length()
        bl = x.bit_length()
        if bl < 70:
            break
        f = rowscore64(val >> (blv - 64))
        fs.append(f)
        if f > best[0]:
            best = (f, r, val >> (blv - 64))
        # same row set for real and pure: the real machine's sea position
        # gates both (otherwise the pure flow gets more rows and wins
        # spuriously)
        if S <= b0 and S + bl >= b0 + 64:
            w = ((m3 >> b0) if pure else (x >> (b0 - S))) & ((1 << 64) - 1)
            ts.append(rowscore64(w))
            ch = trow >> 6
            bi = trow & 63
            for j in range(64):
                cols.setdefault((ch, j), 0)
                cols[(ch, j)] |= ((w >> j) & 1) << bi
            trow += 1
    cs = [rowscore64(wd | (1 << 63)) if False else rowscore64(wd)
          for (ch, j), wd in cols.items() if trow >> 6 > ch]
    return (top3avg(fs), top3avg(ts), top3avg(cs), best)


def main():
    pattern = sys.argv[1]
    T = int(sys.argv[2])
    hits = []
    for path in glob.glob(pattern):
        for line in open(path):
            p = line.split()
            hits.append((int(p[0], 16),) + tuple(map(float, p[1:])))
    hits.sort(key=lambda h: -max(h[1], h[2], h[3]))
    print("%d hits from %s" % (len(hits), pattern))
    mant = tip = lost = vonly = 0
    for h in hits:
        n = h[0]
        if max(h[1], h[2], h[3]) <= 0 and h[4] > 0:
            vonly += 1          # vertical-channel-only hit
            continue
        fr, tr, cr, bestr = channels(n, T)
        fp, tp, cp, bestp = channels(n, T, pure=True)
        dr = max(fr - fp, tr - tp, cr - cp)
        dm = max(abs(fr - fp), abs(tr - tp), abs(cr - cp))
        if dm < 2.0:
            mant += 1
        elif dr > 0:
            tip += 1
        else:
            lost += 1
    print("row-channel: %d mantissa-explained, %d tipped, %d lost; "
          "%d vertical-only (checked separately)" % (mant, tip, lost, vonly))
    # top specimens
    print("top specimens:")
    for h in hits[:6]:
        n = h[0]
        fr, tr, cr, best = channels(n, T)
        print("  %d bits, scores f=%.1f t=%.1f c=%.1f v=%.2f, flash at "
              "step %s: top64 = %s..." %
              (n.bit_length(), h[1], h[2], h[3], h[4], best[1],
               bin(best[2])[2:34] if best[2] else "?"))


if __name__ == "__main__":
    main()
