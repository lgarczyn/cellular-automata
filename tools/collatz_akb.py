#!/usr/bin/env python3
"""The A^(k-1)B family: one pair of blocks, every word length, all composing.

Run: python3 tools/collatz_akb.py

For the word A...AB - k blocks of width L, the last one different - the general
concatenation law of collatz_atlas.py has only one nonzero difference term, at
position k-1, so it collapses to

    A^(k-1)B is persistent  <=>  B = A  mod 3^q,   q = v3(2^(kL) - 1)

and the quota q depends on k only through v3. For L = 5 the quotas run

    k     2  3  4  5  6  7  8  9 10 11 12
    q   3^1  0  1  0  2  0  1  0  1  0  2

so a pair with v3(B - A) >= 2 clears every one of them at once: the SAME two
blocks tile as AB, AAB, AAAB, AAAAB, ... for every k up to 12. That is what the
figure shows - A = #.#.. and B = .###. (difference 9), drawn as k = 2..9, each
one a genuine loop with the period printed.

Pairs with a smaller v3 clear only some k. v3(B - A) = 1 keeps every odd k (free,
since kL is then odd and the quota is zero) and every even k except those where
v3(kL/2) >= 1, i.e. drops k = 6 and 12 out of the list. v3 = 0 keeps only the odd
k. So the family a pair belongs to is read straight off the 3-adic valuation of
its difference, and the table below prints that ladder for several pairs.
"""

import os
from math import gcd, lcm

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

L = 5
KS = range(2, 10)
STEPS = 36
COPIES = 2


def v3(n):
    e = 0
    while n and n % 3 == 0:
        n //= 3
        e += 1
    return e


def quota(n):
    return v3((1 << n) - 1)


def show(x, w):
    return "".join("#" if (int(x) >> i) & 1 else "." for i in range(w))


def word(A, B, k):
    """k blocks: A repeated k-1 times, then B."""
    x = B << ((k - 1) * L)
    for i in range(k - 1):
        x |= A << (i * L)
    return x


def composes(A, B, k):
    return (B - A) % 3 ** quota(k * L) == 0


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
    """Multiplicative order of a mod n, n odd and coprime to a."""
    if n == 1:
        return 1
    e = 1
    for p, k in factor(n).items():
        m = p ** k
        t = p ** (k - 1) * (p - 1)
        for q in factor(t):
            while t % q == 0 and pow(a, t // q, m) == 1:
                t //= q
        e = lcm(e, t)
    return e


def period(x, M):
    """3^T x = x mod M  <=>  (M/gcd(M,x)) | 3^T - 1. None if x never returns."""
    n = M // gcd(M, x)
    if n % 3 == 0:
        return None
    return ord_mod(3, n)


def period_walk(x, M, cap=200000):
    y, n = (3 * x) % M, 1
    while y != x and n < cap:
        y = (3 * y) % M
        n += 1
    return n if y == x else None


def spacetime(x, W, T):
    M = (1 << W) - 1
    rows = []
    for _ in range(T):
        rows.append([(int(x) >> i) & 1 for i in range(W)])
        x = (3 * int(x)) % M
    return np.array(rows)


def ladder(pairs):
    print("which k a pair supports, read off v3(B - A):")
    print("   %-8s %-8s %-4s  %s" % ("A", "B", "v3", "".join(
        "%4d" % k for k in range(2, 13))))
    for A, B in pairs:
        marks = "".join("%4s" % ("Y" if composes(A, B, k) else "-")
                        for k in range(2, 13))
        print("   %-8s %-8s %-4d  %s"
              % (show(A, L), show(B, L), v3(abs(B - A)), marks))
    print()
    print("   quota per k: " + "  ".join("k=%d:3^%d" % (k, quota(k * L))
                                         for k in range(2, 13)))
    print()


def figure(A, B, images):
    fig, axs = plt.subplots(2, 4, figsize=(24, 12), dpi=145)
    colours = ["#7ee6a0", "#4fd1ff", "#ffb347", "#ff5c8a",
               "#c9a0ff", "#8fe36a", "#ffd166", "#6ad7d7"]
    for ax, k, colour in zip(axs.ravel(), KS, colours):
        p = k * L
        copies = COPIES
        W = p * copies
        cell = word(A, B, k)
        letters = "A" * (k - 1) + "B"
        x = cell * (((1 << W) - 1) // ((1 << p) - 1))
        T = period(cell, (1 << p) - 1)
        ax.imshow(spacetime(x, W, STEPS),
                  cmap=ListedColormap(["#0b0b14", colour]),
                  aspect="auto", interpolation="nearest")
        for c in range(0, W + 1, L):
            ax.axvline(c - 0.5, color="#ffffff",
                       lw=1.6 if c % p == 0 else 0.6,
                       alpha=0.8 if c % p == 0 else 0.3)
        ax.set_title("%s   width %d x %d,  period %s"
                     % ("A" * (k - 1) + "B", p, copies,
                        T), fontsize=12)
        ax.set_xlabel("ring cell (W = %d), %d copies of the cell" % (W, copies))
        ax.set_ylabel("step")
        ax.set_yticks([])
        ax.set_xticks([c * p + j * L + L / 2.0 - 0.5
                       for c in range(copies) for j in range(k)])
        ax.set_xticklabels(list(letters) * copies, fontsize=9)
        ax.tick_params(axis="x", length=0)
    fig.suptitle("one pair of blocks, every word length: A = %s, B = %s "
                 "(difference 9, so v3 = 2 clears every quota)"
                 % (show(A, L), show(B, L)), fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-akb.png"), facecolor="white")
    plt.close(fig)


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    A, B = 0b00101, 0b01110           # #.#.. and .###. , difference 9
    print("A = %s, B = %s, B - A = %d, v3 = %d"
          % (show(A, L), show(B, L), B - A, v3(B - A)))
    print()
    print("every word, verified by running it in a ring:")
    print("   %-12s %8s %10s %10s" % ("word", "width", "composes", "period"))
    for k in KS:
        p = k * L
        cell = word(A, B, k)
        M = (1 << p) - 1
        T = period(cell, M)
        ok = composes(A, B, k)
        assert (T is not None) == ok, (k, T, ok)
        if p <= 25:                      # cross-check the algebra against a walk
            assert period_walk(cell, M) == T, (k, T)
        print("   %-12s %8d %10s %10s %s"
              % ("A" * (k - 1) + "B", p, "YES" if ok else "no",
                 T if T else "never returns",
                 "(walk agrees)" if p <= 25 else ""))
    print()

    ladder([(A, B), (0b00101, 0b01000), (0b00101, 0b00110),
            (0b00011, 0b10101)])

    figure(A, B, images)
    print("wrote images/collatz-akb.png")


if __name__ == "__main__":
    main()
