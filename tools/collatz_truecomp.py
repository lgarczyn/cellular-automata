#!/usr/bin/env python3
"""True composition: words whose period is the period of their parts.

Run: python3 tools/collatz_truecomp.py

collatz_akb.py showed the wrong thing. Its words are all PERSISTENT - they close
- but the period explodes as blocks are added:

    AB 30, AAB 150, AAAB 120, AAAAB 450, AAAAAB 1650, AAAAAAB 1,106,280

while the block A on its own cycles in 30. Nothing about A survives into the
composite; the orbit just happens to close eventually. That is not composition.

The right criterion is that the composite keeps the period of its parts, and
there is an exact law for where the blow-up comes from. Since x -> 3x is linear,
split a word into a uniform background plus a difference field,

    X  =  B0 * (2^kL - 1)/(2^L - 1)  +  sum_j (Bj - B0) 2^(jL)
          \___________________/         \______________________/
              background                     defect D

and then

    period(X)  divides  lcm( period(background), period(D) ).

The background is just the block B0 as a crystal, so it contributes exactly the
part's own period. EVERY bit of the blow-up is the defect field. Define a word
to compose TRULY when

    period(word)  divides  lcm of the periods of its distinct blocks

- no new frequencies, the composite lives inside the parts' orbits.

Two results, both exhaustive over all words with minimal spatial period exactly
kL (patterns that merely LOOK like blocks - a period-3 crystal chopped into
5-wide pieces - are excluded; they inflate the count by an order of magnitude):

1. THE A^(k-1)B FAMILY NEVER COMPOSES TRULY FOR k >= 3. Not at any L <= 16.
   The reason is size: the defect is a single number (B - A) 2^((k-1)L) with
   |B - A| < 2^L, so gcd(2^kL - 1, D) < 2^L, and the primitive prime divisors of
   2^kL - 1 - which exceed 2^L for these widths - are left live. They force a
   period no width-L block can match. Confirmed by exhaustive shape census: at
   k = 3 the only shape that ever composes truly is ABC, with all three blocks
   distinct. AAB, ABA, ABB: zero hits, at L = 5 and L = 7 alike.

2. GENUINE ONES DO EXIST, and at k = 2 they can be the whole population:

       L=5  k=2   310 of 310 genuine words compose truly (period 5, parts 30)
       L=6  k=2     6 of  56                              (period 3, parts 6)
       L=7  k=2  5334 of 5334                             (period 42, parts 126)
       L=5  k=3   180 of 32730  (all ABC)
       L=7  k=3  6090 of 2097018  (all ABC)
       L=4  any    0             - 2^4-1 = 15 is too poor in factors

The figure runs each of those for three full periods, so the repeat is visible
rather than asserted, with the blown-up AAB from before as the last panel for
contrast.
"""

import os
from itertools import product
from math import gcd, lcm

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


def v3(n):
    e = 0
    while n and n % 3 == 0:
        n //= 3
        e += 1
    return e


def quota(n):
    return v3((1 << n) - 1)


def is_prime(n):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def rho(n):
    if n % 2 == 0:
        return 2
    c = 1
    while True:
        x = y = 2
        d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = gcd(abs(x - y), n)
        if d != n:
            return d
        c += 1


def factor(n, out=None):
    out = {} if out is None else out
    if n == 1:
        return out
    if is_prime(n):
        out[n] = out.get(n, 0) + 1
        return out
    d = rho(n)
    factor(d, out)
    factor(n // d, out)
    return out


def ord_mod(a, n):
    if n == 1:
        return 1
    e = 1
    for p, k in factor(n).items():
        mm = p ** k
        t = p ** (k - 1) * (p - 1)
        for q in factor(t):
            while t % q == 0 and pow(a, t // q, mm) == 1:
                t //= q
        e = lcm(e, t)
    return e


def periods_mod(M):
    """period(x) for x in Z/M under x -> 3x, as a function. None = never returns."""
    cache = {}

    def T(x):
        n = M // gcd(M, x)
        if n % 3 == 0:
            return None
        if n not in cache:
            cache[n] = ord_mod(3, n)
        return cache[n]
    return T


def show(x, w):
    return "".join("#" if (int(x) >> i) & 1 else "." for i in range(w))


def min_period(X, p):
    for d in range(1, p + 1):
        if p % d == 0 and all(((X >> i) & 1) == ((X >> (i % d)) & 1)
                              for i in range(p)):
            return d
    return p


def shape(w):
    names = {}
    for b in w:
        if b not in names:
            names[b] = chr(65 + len(names))
    return "".join(names[b] for b in w)


def census(L, k):
    """All genuine k-block words at width L; which compose truly, by shape."""
    ML, M = (1 << L) - 1, (1 << (k * L)) - 1
    TL, TM = periods_mod(ML), periods_mod(M)
    blocks = [b for b in range(1 << L) if b % 3 ** quota(L) == 0]
    part = {b: TL(b) for b in blocks}
    total, hits = 0, {}
    for w in product(blocks, repeat=k):
        if len(set(w)) == 1:
            continue
        X = sum(b << (j * L) for j, b in enumerate(w))
        if min_period(X, k * L) != k * L:
            continue
        TW = TM(X)
        if TW is None:
            continue
        total += 1
        target = 1
        for b in set(w):
            target = lcm(target, part[b])
        if target % TW == 0:
            hits.setdefault(shape(w), []).append((TW, target, w))
    return total, hits


def spacetime(cell, p, copies, T):
    W = p * copies
    M = (1 << W) - 1
    x = cell * (M // ((1 << p) - 1))
    rows = []
    for _ in range(T):
        rows.append([(int(x) >> i) & 1 for i in range(W)])
        x = (3 * int(x)) % M
    return np.array(rows)


def panel(ax, w, L, TW, target, colour, tag):
    k = len(w)
    p = k * L
    copies = max(1, int(round(80.0 / p)))
    cell = sum(b << (j * L) for j, b in enumerate(w))
    ax.imshow(spacetime(cell, p, copies, 3 * TW),
              cmap=ListedColormap(["#0b0b14", colour]),
              aspect="auto", interpolation="nearest")
    for c in range(0, p * copies + 1, L):
        ax.axvline(c - 0.5, color="#ffffff",
                   lw=1.6 if c % p == 0 else 0.6,
                   alpha=0.8 if c % p == 0 else 0.3)
    for t in (TW, 2 * TW):
        ax.axhline(t - 0.5, color="#ffffff", lw=1.4, alpha=0.85)
    ax.set_title("%s   %s\nperiod %d,  parts cycle in %d   %s"
                 % (shape(w), "|".join(show(b, L) for b in w),
                    TW, target, tag), fontsize=11)
    ax.set_xlabel("ring cell (W = %d)" % (p * copies))
    ax.set_ylabel("3 full periods")
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    print("exhaustive census - words with minimal spatial period exactly kL:")
    print("   %3s %3s %12s %12s   %s"
          % ("L", "k", "genuine", "true comps", "shapes that ever compose truly"))
    picks = {}
    for L, k in ((4, 2), (4, 3), (5, 2), (5, 3), (6, 2), (6, 3), (7, 2), (7, 3)):
        total, hits = census(L, k)
        n = sum(len(v) for v in hits.values())
        print("   %3d %3d %12d %12d   %s"
              % (L, k, total, n,
                 ", ".join("%s (%d)" % (s, len(hits[s])) for s in sorted(hits))
                 or "-"))
        for s, v in hits.items():
            picks[(L, k, s)] = sorted(v)[0]
    print()
    print("   at k = 3 only ABC ever composes truly - AAB, ABA and ABB never do,")
    print("   because a single-block defect cannot cancel the primitive prime")
    print("   divisors of 2^(3L) - 1, which are larger than 2^L at these widths.")
    print()

    chosen = [((5, 2, "AB"), "#7ee6a0"), ((6, 2, "AB"), "#4fd1ff"),
              ((7, 2, "AB"), "#ffb347"), ((5, 3, "ABC"), "#c9a0ff"),
              ((7, 3, "ABC"), "#6ad7d7")]
    fig, axs = plt.subplots(2, 3, figsize=(22, 13), dpi=145)
    for ax, (key, colour) in zip(axs.ravel(), chosen):
        TW, target, w = picks[key]
        panel(ax, w, key[0], TW, target, colour, "TRUE")

    # contrast: the AAB from collatz_akb.py, which merely persists
    L = 5
    w = (0b00101, 0b00101, 0b01110)
    TM = periods_mod((1 << (3 * L)) - 1)
    TL = periods_mod((1 << L) - 1)
    target = lcm(*[TL(b) for b in set(w)])
    panel(axs[1][2], w, L, TM(sum(b << (j * L) for j, b in enumerate(w))),
          target, "#ff5c8a", "blow-up x5 - persists but does not compose")

    fig.suptitle("true composition: the composite cycles inside its parts' periods "
                 "(white lines mark one period)", fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-truecomp.png"), facecolor="white")
    plt.close(fig)
    print("wrote images/collatz-truecomp.png")


if __name__ == "__main__":
    main()
