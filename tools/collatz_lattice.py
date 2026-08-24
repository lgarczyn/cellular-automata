#!/usr/bin/env python3
"""Coordinate changes that strip the visible structure off the Collatz plot.

Run: python3 tools/collatz_lattice.py [N]      (default 10^7; the committed
images were made at 10^9, which needs ~2 GB of disk for the cache)

Produces, and prints the numbers backing, four things:

  slopes      the line families in the raw plot, found by a Radon-style scan.
              Every peak is a lattice direction (da, db) with slope
              (da+db)/(da - db*log2 3).
  transforms  y recoded as b, then detrended and scaled, until the residual
              has the same distribution at every scale.
  shear       x'' = 1.934*log2 n + 0.0657*s makes the (3,2) family vertical,
              because x'' is exactly the integer 2a - 3b.
  wrap        collapsing all the columns onto one, which lands back on the
              detrended residual - the two routes agree to 5 decimal places.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm, ListedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collatz import IMAGES, K, LOG2_3, chunks, column, decode_recipe, occupancy, shear_x


def line_families(log2n, s, lo, hi):
    """Radon-style scan: shear the occupancy grid and see which slope aligns."""
    NX = NY = 600
    m = (log2n >= lo) & (log2n < hi) & (s < 320)
    gx = ((log2n[m] - lo) / (hi - lo) * (NX - 1)).astype(int)
    gy = (s[m] / 320 * (NY - 1)).astype(int)
    occ = np.zeros((NY, NX))
    np.add.at(occ, (gy, gx), 1.0)
    occ = (occ > 0).astype(float)

    slopes = np.arange(-80, 80.25, 0.25)
    score = []
    for sl in slopes:
        shift = (sl * (hi - lo) / (NX - 1)) / (320 / (NY - 1))
        idx = (np.arange(NY)[:, None] + np.round(shift * np.arange(NX))[None, :]).astype(int) % NY
        score.append((np.take_along_axis(occ, idx, 0).sum(1) ** 2).sum())
    score = np.array(score) / np.mean(score)

    peaks = []
    for i in sorted(np.argsort(-score)[:400]):
        if not peaks or slopes[i] - peaks[-1][0] > 2:
            peaks.append((slopes[i], score[i]))
        elif score[i] > peaks[-1][1]:
            peaks[-1] = (slopes[i], score[i])
    peaks.sort(key=lambda p: -p[1])

    import math
    cand = [(da, db) for da in range(-9, 10) for db in range(-9, 10)
            if (da, db) != (0, 0) and math.gcd(abs(da), abs(db)) == 1
            and abs(da - db * LOG2_3) > 1e-3]

    print("dominant line slopes (d steps / d log2 n), and the lattice move behind each:")
    for sl, sc in peaks[:6]:
        # several directions share a slope; report the shortest that matches
        tol = max(0.6, 0.03 * abs(sl))
        near = [d for d in cand if abs((d[0] + d[1]) / (d[0] - d[1] * LOG2_3) - sl) < tol]
        da, db = min(near, key=lambda d: abs(d[0]) + abs(d[1])) if near else (0, 0)
        if da + db < 0:                       # a line has two directions; show the +steps one
            da, db = -da, -db
        print("   %+7.2f  <- (da,db)=(%2d,%2d), n x 2^%d/3^%d = %.4f, steps %+d"
              % (sl, da, db, da, db, 2.0 ** da / 3 ** db, da + db))


def convergents():
    """The near-misses 2^p ~ 3^q that generate the ever-steeper families."""
    import math
    x = LOG2_3
    terms, v = [], x
    for _ in range(8):
        i = math.floor(v)
        terms.append(i)
        v = 1 / (v - i)
    h0, h1, k0, k1 = 1, terms[0], 0, 1
    print("continued-fraction convergents of log2(3) = %.9f:" % x)
    for i in terms[1:]:
        h0, h1 = h1, i * h1 + h0
        k0, k1 = k1, i * k1 + k0
        print("   %4d/%-4d : 2^%d vs 3^%d off by %+.5f in log2 -> family every %d steps"
              % (h1, k1, h1, k1, h1 - k1 * x, h1 + k1))


def figure_transforms(n_max, log2n, s, b, path):
    z = np.divide(b - 2.4008 * log2n, np.sqrt(log2n), out=np.zeros_like(b), where=log2n > 0)
    fig, axs = plt.subplots(1, 3, figsize=(22, 7), dpi=110)
    axs[0].plot(10.0 ** (log2n * np.log10(2)), s, ",", color="blue", rasterized=True)
    axs[0].set_xscale("log")
    axs[0].set_ylabel("iterations to 1")
    axs[0].set_title("1. log x only: striped fan")
    axs[1].hexbin(log2n, b, gridsize=(400, 180), mincnt=1, norm=LogNorm(), cmap="viridis", linewidths=0)
    axs[1].set_ylabel("b = number of 3n+1 steps")
    axs[1].set_title("2. y recoded as b: the 2.585 quantisation is gone")
    bins = np.linspace(-20, 20, 120)
    for lo, hi in [(1e2, 1e3), (1e3, 1e4), (1e4, 1e5), (1e5, 1e6), (1e6, 1e7)]:
        if hi > n_max:
            break
        m = (log2n >= np.log2(lo)) & (log2n < np.log2(hi))
        axs[2].hist(z[m], bins=bins, density=True, histtype="step", lw=1.6,
                    label="n = %.0e..%.0e  (sd %.2f)" % (lo, hi, z[m].std()))
    axs[2].legend(fontsize=9)
    axs[2].set_title("3. detrended + scaled: one law at every scale")
    axs[2].set_ylabel("density")
    for ax in axs[:2]:
        ax.set_xlabel("Input #" if ax is axs[0] else "log2(n)")
    axs[2].set_xlabel("(b - 2.40 log2 n) / sqrt(log2 n)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def figure_shear(log2n, s, x2, path):
    fig, axs = plt.subplots(1, 3, figsize=(22, 7.5), dpi=115)
    axs[0].plot(log2n, s, ",", color="blue", rasterized=True)
    axs[0].set_xlabel("log2(n)")
    axs[0].set_title("before: descending streaks are the (3,2) family")
    axs[1].plot(x2, s, ",", color="blue", rasterized=True)
    axs[1].set_xlabel("x''")
    axs[1].set_title("after shear: whole dataset")
    k = (x2 > 49) & (x2 < 59) & (s > 150) & (s < 350)
    axs[2].plot(x2[k], s[k], ".", ms=1.3, color="blue")
    for v in np.arange(49, 60):
        axs[2].axvline(v - 0.427, color="red", lw=0.6, alpha=0.5)
    axs[2].set_xlim(49, 59)
    axs[2].set_xlabel("x''   (red = 2a-3b integer columns)")
    axs[2].set_title("zoom: one column per value of 2a-3b")
    for ax in axs:
        ax.set_ylabel("iterations to 1")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def figure_wrap(log2n, s, a, b, x2, path):
    c = column(a, b)
    xr = x2 - c                      # position within the column
    y = (s - 3 * c) / 5              # = 2b - a, aligned so +1 column maps onto itself
    delta = -xr * K / 5

    print("wrap:")
    print("   within-column residual xr = -(5/log2 6)*delta, delta in %.4f..%.4f"
          % (delta.min(), delta.max()))
    print("   so n*3^b/2^a lies in %.3f..1  -> dash width x%.3f"
          % (2 ** -delta.max(), 1 / 2 ** -delta.max()))
    print("   aligned y is always a multiple of 5: %s" % bool(((s - 3 * c) % 5 == 0).all()))
    zz = b - 2.4008 * log2n
    print("   y vs the detrended residual: corr %.5f, slope %.4f (2 - log2 3 = %.5f)"
          % (np.corrcoef(y, zz)[0, 1], np.polyfit(zz, y, 1)[0], 2 - LOG2_3))

    fig, axs = plt.subplots(1, 3, figsize=(23, 8), dpi=140)
    k = (x2 > 49) & (x2 < 59) & (s > 150) & (s < 350)
    axs[0].plot(x2[k], s[k], ".", ms=1.3, color="blue")
    axs[0].set_xlabel("x''")
    axs[0].set_ylabel("iterations to 1")
    axs[0].set_title("sheared: separate columns")
    axs[1].hexbin(xr, s, gridsize=(300, 300), mincnt=1, norm=LogNorm(), cmap="magma_r", linewidths=0)
    axs[1].set_ylabel("iterations to 1")
    axs[1].set_title("wrapped, y = raw steps: rungs interleave")
    axs[2].hexbin(xr, y, gridsize=(300, 200), mincnt=1, norm=LogNorm(), cmap="magma_r", linewidths=0)
    axs[2].set_ylabel("(steps - 3c)/5  =  2b - a")
    axs[2].set_title("wrapped + aligned: no lattice left")
    for ax in axs[1:]:
        ax.set_xlabel("x'' - column index")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def figure_fold(log2n, s, path):
    """Fold at one doubling. Exact, because steps(2n) = steps(n) + 1: every
    octave of n contains a perfect copy of the octave below it, the even half,
    plus new material from the odd half. Folding at a wrong period smears."""
    def grid(period):
        q = log2n / period
        fl = np.floor(q)
        x = ((q - fl) * 1023).astype(np.int32)
        y = (s - np.round(fl * period)).astype(np.int64)
        ok = (y >= 0) & (y < 900)
        G = np.zeros((900, 1024), np.int32)
        np.add.at(G, (y[ok], x[ok]), 1)
        return G

    good, bad = grid(1.0), grid(1.3)
    print("fold: true period %d occupied cells, wrong period (1.3) %d - %.1fx smear"
          % ((good > 0).sum(), (bad > 0).sum(), (bad > 0).sum() / (good > 0).sum()))

    prof = (good > 0).sum(1).astype(float)
    seg = prof[100:700] - prof[100:700].mean()
    sp = np.abs(np.fft.rfft(seg)) ** 2
    fr = np.fft.rfftfreq(len(seg))
    print("      vertical period of the folded pattern: %.3f rows (1 + log2 3 = %.4f)"
          % (1 / fr[np.argmax(sp[1:]) + 1], K))

    fig, axs = plt.subplots(1, 2, figsize=(19, 9), dpi=130)
    for ax, (G, t) in zip(axs, [(good, "folded at one doubling (the true period)\n%d cells - sharp" % (good > 0).sum()),
                                (bad, "control: folded at 1.3 doublings\n%d cells - smeared" % (bad > 0).sum())]):
        rows = np.flatnonzero(G.sum(1) > 0)
        ax.imshow(np.where(G > 0, G, np.nan), origin="lower", aspect="auto",
                  extent=[0, 1, rows.min(), rows.max()], norm=LogNorm(),
                  cmap="magma_r", interpolation="nearest")
        ax.set_title(t, fontsize=13)
        ax.set_xlabel("fractional position within the period")
        ax.set_ylabel("steps - (period-adjusted octave)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000_000
    os.makedirs(IMAGES, exist_ok=True)

    n = np.arange(1, n_max + 1, dtype=np.float64)
    log2n = np.log2(n)
    from collatz import steps as load
    s = np.asarray(load(n_max), np.float64)
    a, b = decode_recipe(s, log2n)
    x2 = shear_x(log2n, s)

    line_families(log2n, s, 16.6, 19.93)
    print()
    convergents()
    print()
    figure_fold(log2n, s, os.path.join(IMAGES, "collatz-fold.png"))
    print()
    figure_transforms(n_max, log2n, s, b, os.path.join(IMAGES, "collatz-transforms.png"))
    figure_shear(log2n, s, x2, os.path.join(IMAGES, "collatz-shear.png"))
    figure_wrap(log2n, s, a, b, x2, os.path.join(IMAGES, "collatz-wrap.png"))


if __name__ == "__main__":
    main()
