#!/usr/bin/env python3
"""An atlas of persistent patterns, and the law that says which ones compose.

Run: python3 tools/collatz_atlas.py

Everything here follows from one change of coordinates. A spatially periodic
state of period p, with cell value X, is the repeating binary expansion of the
fraction

    r = X / (2^p - 1)   in Q/Z,

and the dynamics X -> 3X is just r -> 3r. So a pattern IS a rational number with
odd denominator, and all three of its numbers come straight off that fraction.
Writing r = a/d in lowest terms:

    the pattern is persistent  <=>  3 does not divide d
    its spatial period         =  ord_d(2)
    its temporal period        =  ord_d(3)

That turns "which structures exist" into "which odd denominators are there",
which is a catalogue rather than a search. Part 1 prints it.

COMPOSITION 1 - SUPERPOSITION (same cells, states added). Always allowed:
denominators multiply out to lcm(d1, d2), so the composite is persistent iff both
parts are, and its periods are the lcms. Nothing to check, no compatibility.

COMPOSITION 2 - CONCATENATION (blocks side by side: AB, AAB, ABBA). This one has
a real compatibility relation, and it is a congruence. Write

    q_n = v3(2^n - 1)  =  0 if n odd, else 1 + v3(n/2)

for the "3-adic quota" of a width-n cell: a cell of width n is persistent exactly
when v3(X) >= q_n. Then for k blocks of width L each, with B0 a persistent
pattern in its own right,

    B0 B1 ... B(k-1) is persistent  <=>  sum_j (Bj - B0) 2^(jL) = 0  mod 3^(q_kL)

- the background contributes nothing, and the whole condition falls on the
DIFFERENCES between blocks. Verified exhaustively for L <= 8, k <= 4.

For k = 2 that collapses to something you can read off by eye:

    A and B can sit next to each other  <=>  A = B  mod 3^(q_2L)

so compatibility is an EQUIVALENCE RELATION. Every persistent block carries a
charge

    c = (A / 3^q_L)  mod  3^(q_2L - q_L)

taking one of 3^(q_2L - q_L) values, and two blocks compose iff their charges
match. When q_2L = q_L there is a single class and everything composes with
everything; when L is odd the classes are non-trivial and most pairs are
forbidden. The figure is those matrices, sorted by charge - the block-diagonal
structure is the compatibility relation itself.
"""

import os
from math import gcd, lcm

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


def v3(n):
    e = 0
    while n % 3 == 0:
        n //= 3
        e += 1
    return e


def quota(n):
    """v3(2^n - 1): how much of a 3-adic debt a width-n cell has to pay."""
    return v3((1 << n) - 1)


def order(a, d):
    if d == 1:
        return 1
    k, x = 1, a % d
    while x != 1:
        x = x * a % d
        k += 1
    return k


def totient(d):
    return sum(1 for a in range(1, d + 1) if gcd(a, d) == 1)


def cell_of(a, d, p):
    """The width-p cell whose fraction is a/d."""
    return a * ((1 << p) - 1) // d


def show(x, p):
    return "".join("#" if (int(x) >> i) & 1 else "." for i in range(p))


# --- part 1: the catalogue ---------------------------------------------------

def catalogue(dmax=130):
    rows = []
    for d in range(1, dmax + 1, 2):
        if d % 3 == 0:
            continue
        p, T = order(2, d), order(3, d)
        n = totient(d) if d > 1 else 1
        rows.append((d, p, T, n, n // p if d > 1 else 1))
    return rows


def print_catalogue():
    print("PART 1 - the catalogue. One species per odd denominator d with 3 | d")
    print("false; every persistent pattern in this automaton is in here.")
    print()
    print("   %5s %8s %10s %9s %8s   %s"
          % ("d", "spatial", "temporal", "patterns", "up to", "example cell"))
    print("   %5s %8s %10s %9s %8s   %s"
          % ("", "period", "period", "", "rotation", ""))
    for d, p, T, n, orb in catalogue():
        ex = show(cell_of(1, d, p), p) if d > 1 else "."
        print("   %5d %8d %10d %9d %8d   %s" % (d, p, T, n, orb, ex[:46]))
    print()
    print("   spatial period = ord_d(2), temporal period = ord_d(3), and the")
    print("   pattern is the repeating binary expansion of a/d.")
    print()


# --- part 2: superposition ---------------------------------------------------

def check_superposition():
    print("PART 2 - superposition (two patterns in the same cells). Always legal;")
    print("periods compose by lcm. Checked against direct simulation:")
    print()
    print("   %10s %10s %12s %12s %s"
          % ("d1", "d2", "predicted T", "measured T", "ok"))
    pairs = [(5, 7), (7, 13), (5, 13), (11, 31), (13, 41), (7, 73)]
    for d1, d2 in pairs:
        p = lcm(order(2, d1), order(2, d2))
        M = (1 << p) - 1
        x = (cell_of(1, d1, p) + cell_of(1, d2, p)) % M
        pred = lcm(order(3, d1), order(3, d2))
        k, y = 1, (3 * x) % M
        while y != x:
            y = (3 * y) % M
            k += 1
        print("   %10d %10d %12d %12d %s"
              % (d1, d2, pred, k, "YES" if k == pred else "NO"))
    print()


# --- part 3: concatenation ---------------------------------------------------

def check_concatenation(lmax=7, kmax=4):
    from itertools import product
    print("PART 3 - concatenation (blocks side by side). The whole condition")
    print("falls on the differences between blocks:")
    print()
    print("     B0 B1 ... B(k-1) persistent  <=>  sum_j (Bj - B0) 2^(jL) = 0 mod 3^q")
    print()
    print("   %3s %3s %8s %10s %10s %8s   %s"
          % ("L", "k", "quota", "words", "persistent", "share", "law holds"))
    for L in range(1, lmax + 1):
        qL = quota(L)
        blocks = [A for A in range(1 << L) if A % 3 ** qL == 0]
        for k in range(2, kmax + 1):
            qk = quota(k * L)
            u = 1 << L
            tot = val = match = 0
            for w in product(blocks, repeat=k):
                X = sum(b << (j * L) for j, b in enumerate(w))
                good = X % 3 ** qk == 0
                pred = sum((b - w[0]) * u ** j
                           for j, b in enumerate(w)) % 3 ** qk == 0
                tot += 1
                val += good
                match += (good == pred)
            print("   %3d %3d %8s %10d %10d %7.1f%%   %s"
                  % (L, k, "3^%d" % qk, tot, val, 100.0 * val / tot,
                     "YES" if match == tot else "NO"))
    print()


def charge_table(lmax=12):
    print("   charges - for k = 2 the law is A = B mod 3^q, an equivalence relation,")
    print("   so each persistent block carries a charge and only equal charges compose:")
    print()
    print("   %3s %10s %10s %10s %9s %12s"
          % ("L", "quota L", "quota 2L", "charges", "blocks", "pairs legal"))
    for L in range(1, lmax + 1):
        qL, q2 = quota(L), quota(2 * L)
        m = 3 ** (q2 - qL)
        pop = {}
        n = 0
        for A in range(1 << L):
            if A % 3 ** qL:
                continue
            n += 1
            c = (A // 3 ** qL) % m
            pop[c] = pop.get(c, 0) + 1
        share = sum(v * v for v in pop.values()) / float(n * n)
        print("   %3d %10s %10s %10d %9d %11.1f%%"
              % (L, "3^%d" % qL, "3^%d" % q2, m, n, 100.0 * share))
    print("   (when the two quotas agree there is one charge and composition is free;")
    print("    odd L always splits into 3^(1+v3(L)) classes)")
    print()


# --- part 4: the compatibility matrices --------------------------------------

def matrix(L):
    qL, q2 = quota(L), quota(2 * L)
    blocks = [A for A in range(1 << L) if A % 3 ** qL == 0]
    blocks.sort(key=lambda A: ((A // 3 ** qL) % 3 ** (q2 - qL), A))
    n = len(blocks)
    m = np.zeros((n, n), dtype=np.uint8)
    for i, A in enumerate(blocks):
        for j, B in enumerate(blocks):
            m[i, j] = ((A | (B << L)) % 3 ** q2 == 0)
    return blocks, m, 3 ** (q2 - qL)


def spacetime(x, W, T):
    M = (1 << W) - 1
    rows = []
    for _ in range(T):
        rows.append([(int(x) >> i) & 1 for i in range(W)])
        x = (3 * int(x)) % M
    return np.array(rows)


def figure(images):
    fig, axs = plt.subplots(2, 3, figsize=(23, 14), dpi=145)
    colours = ["#7ee6a0", "#4fd1ff", "#ffb347", "#ff5c8a"]
    for ax, L, colour in zip(axs.ravel()[:4], (5, 6, 7, 9), colours):
        blocks, m, nc = matrix(L)
        ax.imshow(m, cmap=ListedColormap(["#0b0b14", colour]),
                  interpolation="nearest")
        ax.set_title("L = %d   %d blocks, %d charge%s   %.0f%% of pairs compose"
                     % (L, len(blocks), nc, "" if nc == 1 else "s",
                        100.0 * m.sum() / m.size), fontsize=12)
        ax.set_xlabel("block B (sorted by charge)")
        ax.set_ylabel("block A")
        ax.set_xticks([])
        ax.set_yticks([])

    # a legal wall and an illegal one, at L = 9
    L, W, T = 9, 90, 70
    qL, q2 = quota(L), quota(2 * L)
    A = 0b101101101
    good = next(B for B in range(1 << L)
                if B != A and (B - A) % 3 ** q2 == 0)
    bad = next(B for B in range(1 << L)
               if B != A and (B - A) % 3 ** q2 != 0)
    M = (1 << W) - 1
    embed = M // ((1 << (2 * L)) - 1)

    def cycle_length(x):
        y = x
        for _ in range(quota(W) + 1):          # walk off the transient first
            y = (3 * y) % M
        z, k = (3 * y) % M, 1
        while z != y:
            z = (3 * z) % M
            k += 1
        return k

    # left: the legal wall, running
    x = (A | (good << L)) * embed
    ax = axs[1][1]
    ax.imshow(spacetime(x, W, T), cmap=ListedColormap(["#0b0b14", "#8fe36a"]),
              aspect="auto", interpolation="nearest")
    for c in range(0, W + 1, L):
        ax.axvline(c - 0.5, color="#ffffff", lw=0.8, alpha=0.4)
    ax.set_title("A=%s  B=%s   same charge\na permanent wall, period %d"
                 % (show(A, L), show(good, L), cycle_length(x)), fontsize=11)
    ax.set_xlabel("ring cell (W = 90), wall every %d cells" % L)
    ax.set_ylabel("step")
    ax.set_yticks([])

    # right: the illegal one, shown as x_t XOR x_(t+T'). zero means "already on
    # the cycle"; the lit rows at the top are the state being destroyed.
    y = (A | (bad << L)) * embed
    Tc = cycle_length(y)
    rows, z, trans = [], y, 0
    for t in range(12):
        w = z
        for _ in range(Tc):
            w = (3 * w) % M
        d = int(z) ^ int(w)
        if d:
            trans = t + 1
        rows.append([(d >> i) & 1 for i in range(W)])
        z = (3 * z) % M
    ax = axs[1][2]
    ax.imshow(np.array(rows), cmap=ListedColormap(["#0b0b14", "#ff5c8a"]),
              aspect="auto", interpolation="nearest")
    for c in range(0, W + 1, L):
        ax.axvline(c - 0.5, color="#ffffff", lw=0.8, alpha=0.4)
    ax.set_title("A=%s  B=%s   different charge\nx_t XOR x_(t+%d): lit = not yet on a "
                 "cycle (%d steps)" % (show(A, L), show(bad, L), Tc, trans), fontsize=11)
    ax.set_xlabel("ring cell (W = 90)")
    ax.set_ylabel("step")
    ax.set_yticks(range(12))
    ax.set_yticklabels(range(12), fontsize=7)
    fig.suptitle("compatibility atlas - which patterns can be laid side by side",
                 fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-atlas.png"), facecolor="white")
    plt.close(fig)


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)
    print_catalogue()
    check_superposition()
    check_concatenation()
    charge_table()
    figure(images)
    print("wrote images/collatz-atlas.png")


if __name__ == "__main__":
    main()
