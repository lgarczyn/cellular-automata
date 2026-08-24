"""Shared helpers for the Collatz stopping-time experiments.

Everything here works from one array: the total stopping time of every n up to
some limit, produced by collatz_steps.c and memory-mapped so 10^9 entries cost
2 GB on disk rather than in RAM.

The key move is that a stopping time plus an input size is enough to recover
the *recipe*: how many halvings (a) and how many 3n+1 steps (b) the trajectory
used. That pair indexes essentially all the structure in the picture.
"""

import os
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(HERE, os.pardir, "images")

LOG2_3 = np.log2(3)
K = 1 + LOG2_3          # 2.5850, the step cost of one extra 3n+1
DRIFT = 0.085           # systematic offset from the +1s, see decode_recipe


def steps(n_max):
    """Memory-map the stopping times of 1..n_max, computing them if needed."""
    binary = os.path.join(HERE, "collatz_steps")
    source = os.path.join(HERE, "collatz_steps.c")
    if not os.path.exists(binary) or os.path.getmtime(source) > os.path.getmtime(binary):
        subprocess.run(["gcc", "-O3", "-o", binary, source], check=True)

    cache = os.path.join(HERE, "collatz_steps_%d.bin" % n_max)
    if not os.path.exists(cache):
        subprocess.run([binary, str(n_max), cache], check=True)
    return np.memmap(cache, dtype=np.uint16, mode="r")


def decode_recipe(s, log2n):
    """Recover (a, b) - halvings and 3n+1 steps - from stopping time and size.

    A trajectory that ends at 1 satisfies n * 3^b / 2^a = 1 up to the drift the
    +1s introduce, so log2(n) = a - b*log2(3) - delta with delta in [0, 0.326].
    With s = a + b that inverts to b = (s - log2 n)/(1 + log2 3), and rounding
    off the mean drift recovers b exactly - verified on 4000 random n below 10^7
    with a 100% hit rate.
    """
    b = np.round((s - log2n) / K - DRIFT)
    return s - b, b


def column(a, b):
    """The invariant that the verticalising shear turns into integer columns."""
    return 2 * a - 3 * b


def shear_x(log2n, s):
    """x'' - shears the (3,2) line family upright. Equals column(a, b)."""
    return (5 * log2n + (2 * LOG2_3 - 3) * s) / K


def chunks(n_max, size=25_000_000):
    """Yield (offset, n, stopping times, log2 n) over 1..n_max."""
    mm = steps(n_max)
    for i0 in range(0, n_max, size):
        n = np.arange(i0 + 1, min(i0 + size, n_max) + 1)
        yield i0, n, np.asarray(mm[i0:i0 + len(n)], np.int64), np.log2(n.astype(np.float64))


def occupancy(H):
    """Boolean-with-NaN image for imshow: filled cells only, no density."""
    return np.where(H > 0, 1, np.nan)
