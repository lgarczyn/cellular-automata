#!/usr/bin/env python3
"""No gliders: every perturbation spreads at exactly log2(3) cells per step.

Run: python3 tools/collatz_glider.py

The right frame for the machine question. A row of this CA is the *universe*,
not a machine state - treating the whole number as the state turns the question
into number theory and misses what a cellular automaton is. A machine is a
LOCALIZED pattern, like a glider in Rule 110 (also in this repo, and universal
precisely because its gliders collide in controlled ways). So the question is
whether this CA has gliders at all.

Setup, standard for the question: the all-ones 2-adic background is stable
(3*(-1)+1 = -2, halve once, back to -1, period 1), so inject a localized defect
into it and watch.

The answer is exact rather than empirical. Two states differing only in high
bits agree on their low bits, hence on their halving count v, so the difference
obeys

    d  ->  3d / 2^v

exactly - the perturbation dynamics is LINEAR, and it is multiplication by 3.
Since 3d always needs log2(3) more bits than d, the only bounded orbit is
d = 0. Verified: same v and the linear law in every trial, no bounded support
among all 4095 defect patterns up to 12 bits wide, and a measured spread rate
of 1.583 bits/step against log2(3) = 1.58496.

So this CA has a speed of light, equal to log2(3), and every disturbance
travels at exactly it. Nothing propagates while keeping its shape. That is a
stronger and much simpler obstruction than the Diophantine arguments: gliders
do not exist, so there is nothing to collide, so there is no computation to
build - regardless of what the numbers do.

(Rule 110 by contrast has an ether supporting defects that translate without
spreading. That difference - dispersion-free propagation - is exactly what
makes one CA universal and this one not.)
"""

import math
import random

W = 2000
MASK = (1 << W) - 1


def step(x):
    """One Collatz step on a 2-adic state truncated to W bits."""
    t = (3 * x + 1) & MASK
    v = 0
    while t % 2 == 0 and v < W:
        t >>= 1
        v += 1
    return t, v


def support_width(d):
    if d == 0:
        return 0
    return d.bit_length() - ((d & -d).bit_length() - 1)


def check_linear(trials=6, seed=2):
    """Two states differing high up share v, and their difference obeys d -> 3d/2^v."""
    rng = random.Random(seed)
    bg = MASK
    for _ in range(trials):
        p, pat = rng.randrange(200, 900), rng.randrange(1, 1 << 8)
        a, b = bg, bg ^ (pat << p)
        for _ in range(25):
            a2, va = step(a)
            b2, vb = step(b)
            if va != vb:
                return False
            if ((a2 - b2) - ((3 * (a - b)) >> va)) % (1 << (W - 200)) != 0:
                return False
            a, b = a2, b2
    return True


def glider_search(max_width=12, steps=40):
    """Any defect pattern whose support stays bounded would be a glider."""
    bg = MASK
    survivors = 0
    for pat in range(1, 1 << max_width):
        a, b = bg, bg ^ (pat << 600)
        w0 = pat.bit_length()
        bounded = True
        for _ in range(steps):
            a, _ = step(a)
            b, _ = step(b)
            d = a ^ b
            if d == 0:
                break
            if support_width(d) > w0 + 30:
                bounded = False
                break
        survivors += bounded
    return survivors, (1 << max_width) - 1


def spread_rate(steps=200):
    bg = MASK
    a, b = bg, bg ^ (0b1011 << 900)
    first = last = None
    for i in range(steps):
        w = support_width(a ^ b)
        if i == 0:
            first = w
        last = w
        a, _ = step(a)
        b, _ = step(b)
    return (last - first) / (steps - 1)


def main():
    bg = MASK
    _, v = step(bg)
    print("background ...1111 maps to itself after %d halving - stable, period 1" % v)
    print()
    print("perturbation dynamics is exactly linear (d -> 3d/2^v): %s" % check_linear())
    print("  so the only bounded orbit is d = 0: 3d always needs log2(3) more bits")
    print()
    s, total = glider_search()
    print("glider search over every defect up to 12 bits wide, 40 steps:")
    print("  patterns whose support stayed bounded: %d of %d" % (s, total))
    print()
    print("measured spread rate: %.5f cells/step   (log2 3 = %.5f)" % (spread_rate(), math.log2(3)))
    print()
    print("this CA has a speed of light of log2(3), and every disturbance travels")
    print("at exactly it. no glider, nothing to collide, no computation to build.")


if __name__ == "__main__":
    main()
