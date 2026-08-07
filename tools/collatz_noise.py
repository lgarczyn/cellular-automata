#!/usr/bin/env python3
"""How close is the last residual to actual noise? Three probes.

Run: python3 tools/collatz_noise.py [BITS]     (default 24: n < 2^24)

After the peeling in collatz_lattice.py / collatz_dyadic.py, what's left is the
residual z = b - 2.4 log2 n, self-affine on the dyadic tree with 1% of its
variance per bit of n. This script asks whether that cascade is itself
patterned or coin-flip:

  increments  the level-k detail m_k - m_{k-1} of the conditional-mean tree.
              Variance is flat at ~5.7 for fourteen straight levels and the
              correlation between a child's increment and its parent's is
              +0.000 everywhere: the cascade has no memory across levels.

  Walsh       the Walsh-Hadamard spectrum of E[z | n mod 2^16]. Total energy
              per level is constant (the 1%/bit law as a 1/f spectrum), but
              WITHIN a level the energy is not chi-square flat: masks touching
              few bits carry ~2x the energy of their level, masks touching many
              carry ~0.75x. The one detectable pattern inside the noise: the
              residual prefers simple few-bit interactions.

  3-adic      the same variance-per-digit measurement in base 3. After
              correcting for overfitting (a k-digit fit on m samples explains
              3^k/m spuriously), ternary digits carry ~0.0% per digit against
              1.0% per binary bit. The two sides of 3n+1 are completely
              asymmetric: the trajectory reads n's binary digits and is blind
              to its ternary ones.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collatz import IMAGES, decode_recipe, steps

TREND = 2.4008


def walsh(v):
    w = v.copy()
    h = 1
    while h < len(w):
        w = w.reshape(-1, 2, h)
        w = np.concatenate([w[:, 0] + w[:, 1], w[:, 0] - w[:, 1]], axis=1).reshape(-1)
        h *= 2
    return w / np.sqrt(len(v))


def cond_mean(vals, keys, size):
    su = np.zeros(size)
    c = np.zeros(size)
    np.add.at(su, keys, vals)
    np.add.at(c, keys, 1)
    return su / np.maximum(c, 1)


def main():
    bits = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    n_max = 1 << bits
    os.makedirs(IMAGES, exist_ok=True)

    n = np.arange(1, n_max, dtype=np.int64)
    s = np.asarray(steps(n_max)[:n_max - 1], np.int64)
    log2n = np.log2(n.astype(np.float64))
    _, b = decode_recipe(s, log2n)
    z = b - TREND * log2n

    KD = min(16, bits - 6)
    ms = {k: cond_mean(z, (n & ((1 << k) - 1)).astype(np.int64), 1 << k) for k in range(1, KD + 1)}

    # -- increments --------------------------------------------------------
    lv, var, corr = [], [], []
    prev = None
    print("increment variance per level, and correlation with the parent increment:")
    for k in range(2, KD + 1):
        d = ms[k] - ms[k - 1][np.arange(1 << k) & ((1 << (k - 1)) - 1)]
        lv.append(k)
        var.append(d.var())
        if prev is not None:
            corr.append(np.corrcoef(d, prev[np.arange(1 << k) & ((1 << (k - 1)) - 1)])[0, 1])
        prev = d
    for k, v in zip(lv, var):
        print("   level %2d : var %.3f%s" % (k, v, "" if k == 2 else "  parent-corr %+0.3f" % corr[k - 3]))

    # -- Walsh -------------------------------------------------------------
    m0 = ms[KD] - ms[KD].mean()
    E = walsh(m0) ** 2
    mask = np.arange(1 << KD)
    lvl = np.zeros(1 << KD, np.int64)
    lvl[1:] = np.int64(np.floor(np.log2(mask[1:]))) + 1
    pc = np.zeros(1 << KD, np.int64)
    for k in range(KD):
        pc += (mask >> k) & 1

    print("Walsh: total energy per level (flat = the 1%%/bit law):")
    for k in range(2, KD + 1, 2):
        sel = lvl == k
        print("   level %2d : total %9.0f  mean/coeff %9.2f" % (k, E[sel].sum(), E[sel].mean()))
    print("Walsh: energy vs level mean, by how many bits the mask touches (levels 8-14):")
    pratio = []
    for p in range(1, 8):
        rs = [E[(pc == p) & (lvl == k)].mean() / E[lvl == k].mean()
              for k in range(8, 15) if ((pc == p) & (lvl == k)).any()]
        pratio.append(np.mean(rs))
        print("   %d bits : %.2f" % (p, pratio[-1]))

    # -- 3-adic ------------------------------------------------------------
    print("variance explained per digit, base 2 vs base 3 (both overfit-corrected):")
    tot = z.var()
    two, three = [], []
    for k in range(1, 13):
        r = (n & ((1 << k) - 1)).astype(np.int64)
        mu = cond_mean(z, r, 1 << k)
        raw = ((mu[r] - z.mean()) ** 2).mean() / tot
        two.append(100 * (raw - (1 << k) / len(n)) / k)
        r3 = (n % (3 ** k)).astype(np.int64)
        mu3 = cond_mean(z, r3, 3 ** k)
        raw3 = ((mu3[r3] - z.mean()) ** 2).mean() / tot
        three.append(100 * (raw3 - 3 ** k / len(n)) / k)
    print("   base 2: %s" % " ".join("%.2f" % v for v in two))
    print("   base 3: %s" % " ".join("%.2f" % v for v in three))

    # -- figure ------------------------------------------------------------
    plt.rcParams.update({"font.size": 11})
    fig, axs = plt.subplots(2, 2, figsize=(17, 12), dpi=140)

    ax = axs[0, 0]
    ax.bar(lv, var, color="#5470c6")
    ax.axhline(np.median(var), color="#d03020", lw=1, ls="--")
    for k, cc in zip(lv[1:], corr):
        ax.text(k, 0.15, "%+.2f" % cc, ha="center", fontsize=8, color="white", rotation=90)
    ax.set_xlabel("dyadic level k")
    ax.set_ylabel("Var(m_k - m_{k-1})")
    ax.set_title("the cascade has no memory: flat energy, zero parent-correlation\n(white numbers: correlation with the parent's increment)")

    ax = axs[0, 1]
    sub = np.random.default_rng(1).choice(np.arange(1, 1 << KD), 20000, replace=False)
    sc = ax.scatter(mask[sub], E[sub], s=2, c=pc[sub], cmap="viridis", alpha=0.5)
    lm = [2 ** k for k in range(1, KD + 1)]
    ax.plot(lm, [E[lvl == k].mean() for k in range(1, KD + 1)], "r-o", ms=3, lw=1.2, label="level mean ~ 1/mask")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Walsh mask")
    ax.set_ylabel("coefficient energy")
    ax.legend()
    fig.colorbar(sc, ax=ax, label="bits in mask")
    ax.set_title("Walsh spectrum: a 1/f cascade over the bits of n")

    ax = axs[1, 0]
    ax.bar(range(1, 8), pratio, color="#5470c6")
    ax.axhline(1.0, color="#d03020", lw=1, ls="--")
    ax.set_xlabel("number of bits the mask touches")
    ax.set_ylabel("energy / level mean")
    ax.set_title("the one pattern inside the noise:\nsimple few-bit interactions carry double weight")

    ax = axs[1, 1]
    ks = np.arange(1, 13)
    ax.plot(ks, two, "o-", color="#5470c6", label="binary digits of n")
    ax.plot(ks, three, "s-", color="#d03020", label="ternary digits of n")
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("digits of n used (k)")
    ax.set_ylabel("% of residual variance per digit")
    ax.legend()
    ax.set_title("total asymmetry: the trajectory reads n in base 2,\nand is blind to base 3")

    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES, "collatz-noise.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
