#!/usr/bin/env python3
"""Plot Collatz total stopping time vs. input, with a logarithmic x axis.

Stopping times are computed by tools/collatz_steps.c (compiled on demand), then
plotted two ways:

  collatz-log-x.png          every point, as in the classic scatter
  collatz-log-x-density.png  hexbin with a log colour scale, easier to read
                             where the log axis crams points together

Usage: python3 tools/plot_collatz.py [N]   (default N = 10_000_000)
"""

import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, os.pardir, "images")


def stopping_times(n_max):
    """Return an array where index i holds the stopping time of i + 1."""
    binary = os.path.join(HERE, "collatz_steps")
    source = os.path.join(HERE, "collatz_steps.c")
    if not os.path.exists(binary) or os.path.getmtime(source) > os.path.getmtime(binary):
        subprocess.run(["gcc", "-O3", "-o", binary, source], check=True)

    cache = os.path.join(HERE, "collatz_steps_%d.bin" % n_max)
    if not os.path.exists(cache):
        subprocess.run([binary, str(n_max), cache], check=True)
    return np.fromfile(cache, dtype=np.uint16)


def style_axes(ax, n_max):
    ax.set_xscale("log")
    ax.set_xlim(1, n_max)
    ax.set_xlabel("Input #", fontsize=13)
    ax.set_ylabel("Iterations to 1", fontsize=13)
    ax.tick_params(labelsize=11)


def plot_scatter(n, steps, path):
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=140)
    # ',' is the one-pixel marker: the only sane way to draw 10M points.
    ax.plot(n, steps, ",", color="blue", rasterized=True)
    style_axes(ax, n[-1])
    ax.set_ylim(0, steps.max() * 1.02)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_density(n, steps, path):
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=140)
    hb = ax.hexbin(
        n, steps,
        xscale="log", gridsize=(420, 190), mincnt=1,
        norm=LogNorm(), cmap="viridis", linewidths=0,
    )
    style_axes(ax, n[-1])
    ax.set_ylim(0, steps.max() * 1.02)
    fig.colorbar(hb, ax=ax, label="inputs per bin")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000_000
    steps = stopping_times(n_max)
    n = np.arange(1, n_max + 1, dtype=np.float64)

    os.makedirs(OUT_DIR, exist_ok=True)
    plot_scatter(n, steps, os.path.join(OUT_DIR, "collatz-log-x.png"))
    plot_density(n, steps, os.path.join(OUT_DIR, "collatz-log-x-density.png"))
    print("max %d iterations at n = %d" % (steps.max(), int(steps.argmax()) + 1))


if __name__ == "__main__":
    main()
