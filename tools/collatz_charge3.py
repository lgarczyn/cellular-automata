#!/usr/bin/env python3
"""The k >= 3 weighted charge law: mutually forbidden blocks that compose anyway.

SCOPE [x3-bulk]. Everything here is about pure multiplication by 3 on a ring,
x -> 3x mod (2^W - 1) (ca-mul3.js, "the bulk"). Nothing here is a claim about
the real Collatz automaton (CA.CollatzStep).

Run: /usr/bin/python3 tools/collatz_charge3.py

THE LAW. Write a k-block word of width-L blocks MSB-first as B(k-1)...B1B0
(B0 least significant, drawn rightmost), X = sum_j Bj 2^(jL). With

    q_n = v3(2^n - 1) = 0 if n odd, else 1 + v3(n)

the word is persistent (recurs exactly under x -> 3x mod 2^(kL) - 1) iff
v3(X) >= q_(kL). Each persistent block already has v3(Bj) >= q_L, so put
b_j = Bj / 3^(q_L) (the refined charge). Because

    2^L = -1 mod 3^(1+v3(L))   for odd L,      2^L = 1 mod 3   for even L,

the weighted sum sum_j b_j u^j (u = 2^L) collapses, and the whole hierarchy is:

    k=2:  b0 = b1 mod 3^(q_2L - q_L)          nontrivial iff L odd (charge law)
    k=3:  L odd:  FREE (q_3L = 0, 3L is odd)
          L even: b0 + b1 + b2 = 0 mod 3      (refined charges sum to zero)
    k=4:  L odd:  b0 - b1 + b2 - b3 = 0 mod 3^(1+v3(L))   (alternating sum)
          L even: FREE (q_4L = q_L)

The 3-adic debt is a property of EVEN window widths only (3 | 2^n - 1 iff n
even), which is why the hierarchy alternates: blocks clash pairwise, but an odd
number of them together owes nothing, and four of them owe the ALTERNATING sum.

CONSEQUENCE 1 (k=3, the task's phenomenon): for odd L >= 3, pick A, B, C in
three different charge classes mod 3^(1+v3(L)). No pair among AB, BC, AC is
persistent as a 2-block word, yet ABC persists - the triple quota q_3L is zero.
Census (exhaustive, ordered triples of persistent blocks; "strict" = triple
persists AND all three pairs fail):

      L   q_L  q_2L  q_3L  blocks  charges  triples-persist  strict  converse
      1    0    1     0       2       2              8            0        0
      2    1    1     2       2       1              2            0        6
      3    0    2     0       8       8            512          336        0
      4    1    1     2       6       1             72            0      144
      5    0    1     0      32       3          32768         7260        0
      6    2    2     3       8       1            170            0      342
      7    0    1     0     128       3        2097152       465948        0
      8    1    1     2      86       1         212018            0   424038

Strict triples exist iff L is odd and at least 3 charge classes are populated
(L = 1 has only 2 blocks, hence 0). At odd L every triple persists (q_3L = 0)
and the strict count is exactly the ordered triples with pairwise-distinct
charges. "converse" is the mirror phenomenon at even L: there q_2L = q_L makes
every pair legal, but q_3L = q_L + 1 makes the TRIPLE law bite - triples of
mutually compatible blocks that refuse to compose (refined charges must sum to
0 mod 3).

CONSEQUENCE 2 (k=4): a 4-word with ALL SIX pairs forbidden persists iff the
alternating charge sum vanishes; that needs >= 4 populated charge classes, i.e.
3^(1+v3(L)) >= 4: odd L divisible by 3. In range: only L = 3 (240 such words of
8^4 = 4096; next case L = 9). Order matters - (1,2,5,4) has 1-2+5-4 = 0 mod 9
and persists, the SAME multiset as (1,2,4,5) has 1-2+4-5 = -2 and decays.
Arrangement classes for one forbidden pair A,B (charges differ): AB and ABAB
decay (alternating sum 2(a-b) != 0) but AAB, ABB, ABA (odd length: free) and
ABBA, AABB (alternating sum zero) all persist - palindromic and balanced
arrangements rescue a forbidden pair.

VERIFIED BY SIMULATION (L = 3, A,B,C,D = 1,2,5,4; direct iteration, exact
first-return; "xN" = N copies on a wider ring):

    ABC  W=9   v3=0>=q=0  returns, period 12      (also x3 W=27, x5 W=45: 12)
    AB   W=6   v3=0< q=2  never returns: transient 2, alien 6-cycle
    BC   W=6   v3=0< q=2  never returns: transient 2, alien 6-cycle
    AC   W=6   v3=0< q=2  never returns: transient 2, fixed point 0
    ABCD W=12  v3=2>=q=2  returns, period 12      (x3 W=36: v3=3>=q=3, 12)
    ABDC W=12  v3=0< q=2  never returns: transient 2  (x3 W=36: v3=1<q=3)
    ABBA W=12  v3=2>=q=2  returns, period 12
    AABB W=12  v3=3>=q=2  returns, period 12
    ABAB W=12  v3=0< q=2  never returns: transient 2

Writes images/collatz-charge3.png: the strict triple ABC over 3 full periods
(block boundaries marked) beside its decaying pair AB, and the strict 4-word
ABCD beside its decaying reordering ABDC. MSB left, square cells.
"""

import os
from itertools import product

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
    """q_n = v3(2^n - 1) = 0 if n odd, else 1 + v3(n)."""
    return v3((1 << n) - 1)


def word_val(w, L):
    """MSB-first word: w[0] is the leftmost (most significant) block."""
    k = len(w)
    return sum(b << ((k - 1 - j) * L) for j, b in enumerate(w))


def persists(w, L):
    return word_val(w, L) % 3 ** quota(len(w) * L) == 0


def replicate(cell, p, copies):
    W = p * copies
    return cell * (((1 << W) - 1) // ((1 << p) - 1)), W


def orbit(x, W, cap=10 ** 7):
    """(transient, cycle_length, returns_exactly) of x under x -> 3x mod 2^W-1."""
    M = (1 << W) - 1
    seen = {x: 0}
    y, t = x, 0
    while t < cap:
        y = 3 * y % M
        t += 1
        if y in seen:
            return seen[y], t - seen[y], seen[y] == 0
        seen[y] = t
    raise RuntimeError("orbit cap exceeded")


# --- part 1: k = 3 census ----------------------------------------------------

def census_k3(lmax=8):
    print("PART 1 [x3-bulk] - k = 3 census. Ordered triples (A,B,C) of")
    print("persistent width-L blocks; word ABC persistent iff v3(X) >= q_3L;")
    print("pair law: equal charge mod 3^q_2L. strict = ABC persists AND all")
    print("of AB, BC, AC fail. converse = all pairs legal AND ABC fails.")
    print()
    print("   %3s %4s %5s %5s %7s %8s %10s %9s %9s" %
          ("L", "q_L", "q_2L", "q_3L", "blocks", "charges",
           "persist", "strict", "converse"))
    examples = {}
    for L in range(1, lmax + 1):
        qL, q2, q3 = quota(L), quota(2 * L), quota(3 * L)
        m2 = 3 ** q2
        blocks = [b for b in range(1 << L) if b % 3 ** qL == 0]
        charges = len(set(b % m2 for b in blocks))
        n_ok = n_strict = n_conv = 0
        for w in product(blocks, repeat=3):
            A, B, C = w
            ok = persists(w, L)
            fail = ((A - B) % m2 != 0, (B - C) % m2 != 0, (A - C) % m2 != 0)
            n_ok += ok
            if ok and all(fail):
                n_strict += 1
                if L not in examples:
                    examples[L] = w
            if not ok and not any(fail):
                n_conv += 1
        print("   %3d %4d %5d %5d %7d %8d %10d %9d %9d" %
              (L, qL, q2, q3, len(blocks), charges, n_ok, n_strict, n_conv))
    print()
    print("   strict > 0 exactly when L is odd (q_3L = 0 frees the triple while")
    print("   q_2L = 1 + v3(L) > q_L = 0 forbids the pairs) AND >= 3 charge")
    print("   classes are populated - L = 1 has only 2 blocks. At even L the")
    print("   mirror happens: q_2L = q_L legalises every pair, but q_3L = q_L + 1")
    print("   forces refined charges b = B/3^q_L to satisfy b0+b1+b2 = 0 mod 3,")
    print("   so 'converse' triples of mutually legal blocks refuse to compose.")
    print("   first strict examples:",
          "  ".join("L=%d:%s" % (L, examples[L]) for L in sorted(examples)))
    print()


# --- part 2: k = 4 census ----------------------------------------------------

def census_k4(lmax=8, brute_max=6):
    print("PART 2 [x3-bulk] - k = 4 census. 4-words persisting with ALL SIX")
    print("pairs forbidden. Law for odd L: b0 - b1 + b2 - b3 = 0 mod 3^(1+v3(L))")
    print("(u = 2^L = -1), so this needs >= 4 populated charge classes: odd L")
    print("divisible by 3.")
    print()
    print("   %3s %5s %5s %7s %12s %14s   %s" %
          ("L", "q_2L", "q_4L", "blocks", "persist", "strict", "method"))
    for L in range(1, lmax + 1):
        q2, q4 = quota(2 * L), quota(4 * L)
        assert q2 == q4, "pair and 4-word quotas always agree"
        m2 = 3 ** q2
        blocks = [b for b in range(1 << L) if b % 3 ** quota(L) == 0]
        if L <= brute_max:
            n_ok = n_strict = 0
            for w in product(blocks, repeat=4):
                ok = persists(w, L)
                n_ok += ok
                if ok and all((w[i] - w[j]) % m2
                              for i in range(4) for j in range(i + 1, 4)):
                    n_strict += 1
            how = "brute force"
        else:
            # the laws only see b mod 3^q2: count charge classes with sizes
            pop = {}
            for b in blocks:
                pop[b % m2] = pop.get(b % m2, 0) + 1
            u = pow(2, L, m2)
            n_ok = n_strict = 0
            for cw in product(pop, repeat=4):
                mult = 1
                for c in cw:
                    mult *= pop[c]
                if sum(c * pow(u, 3 - j, m2)
                       for j, c in enumerate(cw)) % m2 == 0:
                    n_ok += mult
                    if all((cw[i] - cw[j]) % m2
                           for i in range(4) for j in range(i + 1, 4)):
                        n_strict += mult
            how = "charge classes"
        print("   %3d %5d %5d %7d %12d %14d   %s" %
              (L, q2, q4, len(blocks), n_ok, n_strict, how))
    print()
    print("   only L = 3 in range (240 words); the next case is L = 9, where")
    print("   3^(1+v3(9)) = 27 charge classes exist. Order matters: (1,2,5,4)")
    print("   persists, its reordering (1,2,4,5) decays - the law is a weighted")
    print("   sum, not a set condition.")
    print()
    print("   arrangement classes for one forbidden pair (L=3, A=1, B=2):")
    for w in [(1, 2), (1, 1, 2), (1, 2, 2), (1, 2, 1),
              (1, 2, 2, 1), (1, 1, 2, 2), (1, 2, 1, 2)]:
        name = "".join("AB"[b - 1] for b in w)
        print("      %-4s  %s" % (name,
              "persists" if persists(w, 3) else "decays"))
    print("   odd length is free; even length needs alternating sum zero, so")
    print("   ABBA and AABB rescue the pair while AB and ABAB decay.")
    print()


# --- part 3: simulation ------------------------------------------------------

def simulate():
    print("PART 3 [x3-bulk] - direct simulation, exact first return.")
    print()
    L = 3
    rows = []
    for tag, w, copies in [
            ("ABC ", (1, 2, 6), 1), ("ABCx3", (1, 2, 6), 3),
            ("ABCx5", (1, 2, 6), 5),
            ("AB  ", (1, 2), 1), ("ABx4", (1, 2), 4),
            ("BC  ", (2, 6), 1), ("AC  ", (1, 6), 1),
            ("ABCD", (1, 2, 5, 4), 1), ("ABCDx3", (1, 2, 5, 4), 3),
            ("ABDC", (1, 2, 4, 5), 1), ("ABDCx3", (1, 2, 4, 5), 3),
            ("ABBA", (1, 2, 2, 1), 1), ("AABB", (1, 1, 2, 2), 1),
            ("ABAB", (1, 2, 1, 2), 1)]:
        p = len(w) * L
        x, W = replicate(word_val(w, L), p, copies)
        s, T, ret = orbit(x, W)
        pred = v3(x) >= quota(W)
        assert ret == pred, "v3 criterion must match simulation"
        print("   %-7s %-12s W=%2d  v3(X)=%d q_W=%d  %s" %
              (tag, w, W, v3(x), quota(W),
               "returns exactly, period %d" % T if ret
               else "never returns (transient %d, alien %d-cycle)" % (s, T)))
        rows.append((tag, w, W, s, T, ret))
    print()
    print("   the strict triple (1,2,6) keeps period 12 on W = 9, 27, 45 while")
    print("   every one of its pairs dies in 2 steps; the strict 4-word")
    print("   (1,2,5,4) keeps period 12 on W = 12 and 36 while its reordering")
    print("   (1,2,4,5) dies. Replication never changes the verdict: m copies")
    print("   are the same rational a/d, and the v3 deficit is preserved.")
    print()
    return rows


# --- part 4: the figure ------------------------------------------------------

BG = "#0b0b14"


def spacetime(x, W, T):
    """T rows of the ring, MSB LEFT (column 0 = bit W-1)."""
    M = (1 << W) - 1
    rows = []
    for _ in range(T):
        rows.append([(int(x) >> (W - 1 - c)) & 1 for c in range(W)])
        x = 3 * int(x) % M
    return np.array(rows)


def xor_view(x, W, T, Tc):
    """x_t XOR x_(t+Tc): lit = not yet on the eventual cycle."""
    M = (1 << W) - 1
    rows, z = [], x
    for _ in range(T):
        wv = z
        for _ in range(Tc):
            wv = 3 * wv % M
        d = int(z) ^ int(wv)
        rows.append([(d >> (W - 1 - c)) & 1 for c in range(W)])
        z = 3 * z % M
    return np.array(rows)


def decorate(ax, W, L, p, labels):
    for c in range(0, W + 1, L):
        ax.axvline(c - 0.5, color="#ffffff",
                   lw=1.6 if c % p == 0 else 0.6,
                   alpha=0.8 if c % p == 0 else 0.35)
    k = W // L
    ax.set_xticks([j * L + (L - 1) / 2.0 for j in range(k)])
    ax.set_xticklabels(labels, fontsize=11, color="#333333")
    ax.tick_params(axis="x", length=0, labeltop=True, labelbottom=False, top=False)
    ax.set_yticks([])


def figure(images):
    L, rows = 3, 36
    fig, axs = plt.subplots(2, 2, figsize=(15.5, 14.5), dpi=150)

    # persisting strict triple ABC, 3 copies, 3 full periods
    w = (1, 2, 6)
    x, W = replicate(word_val(w, L), 3 * L, 3)
    _, T, _ = orbit(x, W)
    ax = axs[0][0]
    ax.imshow(spacetime(x, W, rows), cmap=ListedColormap([BG, "#7ee6a0"]),
              interpolation="nearest")
    for t in (T, 2 * T):
        ax.axhline(t - 0.5, color="#ffffff", lw=1.4, alpha=0.85)
    decorate(ax, W, L, 3 * L, ["A", "B", "C"] * 3)
    ax.set_title("strict triple ABC = (1,2,6): charges 1,2,6 mod 9,\n"
                 "all pairs forbidden - yet it returns exactly, period %d" % T,
                 fontsize=11)
    ax.set_xlabel("ring cell (W = %d, 3 copies), MSB left" % W)
    ax.set_ylabel("step (3 full periods, white lines)")

    # its pair AB, decaying: XOR view
    w = (1, 2)
    x, W = replicate(word_val(w, L), 2 * L, 4)
    s, Tc, ret = orbit(x, W)
    assert not ret
    ax = axs[0][1]
    ax.imshow(xor_view(x, W, rows, Tc), cmap=ListedColormap([BG, "#ff5c8a"]),
              interpolation="nearest")
    decorate(ax, W, L, 2 * L, ["A", "B"] * 4)
    ax.set_title("its pair AB = (1,2): charges 1 vs 2 mod 9, v3 deficit 2\n"
                 "x_t XOR x_(t+%d): lit = not yet on a cycle - dead in %d steps"
                 % (Tc, s), fontsize=11)
    ax.set_xlabel("ring cell (W = %d, 4 copies), MSB left" % W)
    ax.set_ylabel("step (never returns to x_0)")

    # strict 4-word ABCD, all six pairs forbidden
    w = (1, 2, 5, 4)
    x, W = replicate(word_val(w, L), 4 * L, 3)
    _, T, _ = orbit(x, W)
    ax = axs[1][0]
    ax.imshow(spacetime(x, W, rows), cmap=ListedColormap([BG, "#4fd1ff"]),
              interpolation="nearest")
    for t in (T, 2 * T):
        ax.axhline(t - 0.5, color="#ffffff", lw=1.4, alpha=0.85)
    decorate(ax, W, L, 4 * L, ["A", "B", "C", "D"] * 3)
    ax.set_title("strict 4-word ABCD = (1,2,5,4): six forbidden pairs,\n"
                 "alternating sum 1-2+5-4 = 0 mod 9 - returns, period %d" % T,
                 fontsize=11)
    ax.set_xlabel("ring cell (W = %d, 3 copies), MSB left" % W)
    ax.set_ylabel("step (3 full periods, white lines)")

    # the same multiset reordered: ABDC decays
    w = (1, 2, 4, 5)
    x, W = replicate(word_val(w, L), 4 * L, 3)
    s, Tc, ret = orbit(x, W)
    assert not ret
    ax = axs[1][1]
    ax.imshow(xor_view(x, W, rows, Tc), cmap=ListedColormap([BG, "#ffb347"]),
              interpolation="nearest")
    decorate(ax, W, L, 4 * L, ["A", "B", "D", "C"] * 3)
    ax.set_title("same blocks reordered ABDC = (1,2,4,5):\n"
                 "1-2+4-5 = -2 mod 9 - x_t XOR x_(t+%d), dead in %d steps"
                 % (Tc, s), fontsize=11)
    ax.set_xlabel("ring cell (W = %d, 3 copies), MSB left" % W)
    ax.set_ylabel("step (never returns to x_0)")

    fig.suptitle("[x3-bulk] the weighted charge law at k >= 3: blocks that "
                 "refuse pairwise still compose as words (L = 3)", fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-charge3.png"), facecolor="white")
    plt.close(fig)


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)
    census_k3()
    census_k4()
    simulate()
    figure(images)
    print("wrote images/collatz-charge3.png")


if __name__ == "__main__":
    main()
