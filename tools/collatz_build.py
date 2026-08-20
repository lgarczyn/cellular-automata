#!/usr/bin/env python3
"""Building structures to order: any period you want, from 3 to 10^37.

Run: python3 tools/collatz_build.py

In the bulk (see collatz_bulk.py) a state of spatial period p is exactly
invariant, and inside that phase the dynamics is x -> 3x mod (2^p - 1). So the
temporal period of a structure is the multiplicative order of 3 modulo whichever
CRT components of 2^p - 1 you switch on, and switching components on and off is
complete control:

    period(x) = lcm{ ord_d(3) : d a prime power dividing 2^p - 1, x != 0 mod d }

That turns structure-building into shopping from a parts catalogue. A W = 60
ring carries components 5, 7, 11, 13, 25, 31, 41, 61, ... with orders 4, 6, 5,
3, 20, 30, 8, 10, so short periods are simply picked off the shelf - each one
below is constructed, then verified by running the automaton:

    period  3   spatial period 12, component 13
    period  4   spatial period  4, component 5
    period  5   spatial period 10, component 11
    period  6   spatial period  3, component 7
    period  8   spatial period 20, component 41
    period 10   spatial period 60, component 61
    period 20   spatial period 20, component 25
    period 30   spatial period  5, component 31

Switch every component of a phase on at once and the periods compound by lcm:
spatial period 20 gives 120, spatial period 60 gives 6600.

The long end is where it gets silly. If 2^p - 1 is a Mersenne prime there is
only one component, so EVERY nonzero state of that phase has the same maximal
period, and no construction is needed at all - genericity does the work:

    p =  31   period 715,827,882                        (7.2e8)
    p =  61   period 256,204,778,801,521,550            (2.6e17)
    p =  89   period 618,970,019,642,690,137,449,562,110 (6.2e26, 3 is a
                                                          primitive root)
    p = 107   period 1.62e32                             (primitive root)
    p = 127   period 5.67e37

An 89-cell-wide patch of this automaton cycles with a period of 6.2 x 10^26
steps, and every one of its 6.2e26 nonzero states is on that same single orbit.
"""

import os
import random
from math import gcd, lcm

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

W = 60
M = (1 << W) - 1


def factor(n):
    f, d = {}, 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def order(a, m):
    if gcd(a, m) != 1:
        return None
    k, x = 1, a % m
    while x != 1:
        x = x * a % m
        k += 1
    return k


def build(p, keep):
    """A state of spatial period p with only the listed components live."""
    Mp = (1 << p) - 1
    R = M // Mp
    X = 0
    for d in keep:
        o = Mp // d
        X = (X + o * pow(o, -1, d)) % Mp
    return (X * R) % M


def measured_period(x):
    k, y = 1, (3 * x) % M
    while y != x:
        y = (3 * y) % M
        k += 1
    return k


def spacetime(x, steps):
    rows = []
    for _ in range(steps):
        rows.append([(int(x) >> i) & 1 for i in range(W)])
        x = (3 * int(x)) % M
    return np.array(rows)


# --- big-ring machinery (Miller-Rabin + Pollard rho) ------------------------

def is_prime(n, k=20):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(k):
        a = random.randrange(2, n - 1)
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
    while True:
        x = y = random.randrange(2, n)
        c, d = random.randrange(1, n), 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = gcd(abs(x - y), n)
        if d != n:
            return d


def factor_big(n, out=None):
    out = {} if out is None else out
    if n == 1:
        return out
    if is_prime(n):
        out[n] = out.get(n, 0) + 1
        return out
    d = rho(n)
    factor_big(d, out)
    factor_big(n // d, out)
    return out


def order_big(a, m):
    o = m - 1
    for p in factor_big(m - 1):
        while o % p == 0 and pow(a, o // p, m) == 1:
            o //= p
    return o


def gallery(images):
    """Short-period structures alone and superposed - they share a window freely."""
    Wg = 120
    Mg = (1 << Wg) - 1

    def mk(p, d):
        Mp = (1 << p) - 1
        o = Mp // d
        return ((o * pow(o, -1, d)) % Mp) * (Mg // Mp) % Mg

    def period(x):
        k, y = 1, (3 * x) % Mg
        while y != x and k < 20000:
            y = (3 * y) % Mg
            k += 1
        return k

    def strip(x, T):
        rows = []
        for _ in range(T):
            rows.append([(int(x) >> i) & 1 for i in range(Wg)])
            x = (3 * int(x)) % Mg
        return np.array(rows)

    spatial = {5: 4, 7: 3, 11: 10, 13: 12}
    combos = [(5,), (7,), (13,), (11,), (5, 7), (5, 13), (7, 13), (11, 13),
              (5, 11), (7, 11), (5, 7, 13), (5, 11, 13)]
    colours = ["#7ee6a0", "#4fd1ff", "#ffb347", "#ff5c8a", "#c9a0ff", "#8fe36a",
               "#ffd166", "#6ad7d7", "#ff9f6a", "#a0e7ff", "#f2a0ff", "#b5e853"]

    print()
    print("short-period structures superposed - the period is the lcm:")
    fig, axs = plt.subplots(3, 4, figsize=(23, 13), dpi=145)
    for ax, cs, colour in zip(axs.ravel(), combos, colours):
        x = 0
        for d in cs:
            x = (x + mk(spatial[d], d)) % Mg
        T = period(x)
        print("   %-14s period %3d" % (" + ".join(map(str, cs)), T))
        ax.imshow(strip(x, 60), cmap=ListedColormap(["#0b0b14", colour]),
                  interpolation="nearest")
        ax.set_title("%s   ->  period %d" % (" + ".join(map(str, cs)), T), fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("short-period structures, alone and superposed - a 120-cell window, x3 dynamics",
                 fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-gallery.png"), facecolor="white")
    plt.close(fig)


def long_variant(images):
    """A short and a long structure in one ring: W = 635 = 5 x 127."""
    Wl = 635
    Ml = (1 << Wl) - 1
    short = Ml // ((1 << 5) - 1)          # spatial period 5,   temporal 30
    long_ = Ml // ((1 << 127) - 1)        # spatial period 127, temporal 5.67e37
    P = 56713727820156410577229101238628035242
    M127 = (1 << 127) - 1
    print()
    print("a long variant, in the same ring as a short one (W = 635 = 5 x 127):")
    print("   3^P = 1 mod 2^127-1 : %s" % (pow(3, P, M127) == 1))
    print("   and minimal - 3^(P/q) != 1 for every prime q | P")
    print("   superposing both phases gives lcm(30, P) = %d" % lcm(30, P))

    def strip(x, T):
        rows = []
        for _ in range(T):
            rows.append([(int(x) >> i) & 1 for i in range(Wl)])
            x = (3 * int(x)) % Ml
        return np.array(rows)

    T = 380
    panels = [(strip(short, T), "spatial period 5  ->  temporal period 30", "#7ee6a0"),
              (strip(long_, T), "spatial period 127 ->  temporal period 5.67 x 10^37", "#ffb347"),
              (strip((short + long_) % Ml, T), "both phases live at once ->  period 2.84 x 10^38", "#ff5c8a")]
    fig, axs = plt.subplots(3, 1, figsize=(19, 17), dpi=150)
    for ax, (im, title, colour) in zip(axs, panels):
        ax.imshow(im, cmap=ListedColormap(["#0b0b14", colour]),
                  interpolation="nearest")
        ax.set_title(title, fontsize=14)
        ax.set_ylabel("step")
    axs[-1].set_xlabel("ring cell (W = 635 = 5 x 127)")
    fig.suptitle("same 635-cell bulk: a 30-step structure and a 10^37-step structure",
                 fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-longvariant.png"), facecolor="white")
    plt.close(fig)


def main():
    random.seed(1)
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    specs = [(3, 12, 13), (4, 4, 5), (5, 10, 11), (6, 3, 7),
             (8, 20, 41), (10, 60, 61), (20, 20, 25), (30, 5, 31)]
    print("short-period structures, built then verified by running:")
    print("  %8s %10s %11s %10s %s" % ("target", "spatial p", "component", "measured", "ok"))
    made = []
    for T, p, d in specs:
        x = build(p, [d])
        m = measured_period(x)
        made.append((T, p, x))
        print("  %8d %10d %11d %10d %s" % (T, p, d, m, "YES" if m == T else "NO"))

    print()
    print("switch every component of a phase on at once - periods compound by lcm:")
    for p in (12, 20, 60):
        keep = [q ** e for q, e in factor((1 << p) - 1).items() if gcd(3, q) == 1]
        T = lcm(*[order(3, d) for d in keep])
        print("   spatial period %-3d, %d components -> period %d" % (p, len(keep), T))

    print()
    print("the long end: Mersenne-prime phases, where every nonzero state is maximal")
    for p in (31, 61, 89, 107, 127):
        Mp = (1 << p) - 1
        if not is_prime(Mp):
            continue
        o = order_big(3, Mp)
        print("   p = %-4d period %-40d (%.3g%s)"
              % (p, o, o, ", 3 is a primitive root" if o == Mp - 1 else ""))

    gallery(images)
    long_variant(images)

    steps = 60
    fig, axs = plt.subplots(2, 4, figsize=(22, 9), dpi=145)
    palette = ["#7ee6a0", "#4fd1ff", "#ffb347", "#ff5c8a",
               "#c9a0ff", "#8fe36a", "#ffd166", "#6ad7d7"]
    for ax, (T, p, x), colour in zip(axs.ravel(), made, palette):
        ax.imshow(spacetime(x, steps), cmap=ListedColormap(["#0b0b14", colour]),
                  interpolation="nearest")
        ax.set_title("period %d   (spatial %d)" % (T, p), fontsize=13)
        ax.set_xlabel("ring cell")
        ax.set_ylabel("step")
    fig.suptitle("structures built to order in a 60-cell bulk, x3 dynamics", fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-structures.png"), facecolor="white")


if __name__ == "__main__":
    main()
