#!/usr/bin/env python3
"""Hex renderer for the real automaton, matching ca-renderer.js _renderHexGrid.

Pointy-top hexagons; MSB on the LEFT (column dc = width-1-c), each row shifted
right by half a hex, so the diagonal-band layout of CA.CollatzStep shows the way
it does in the app's hex view. Cell colors follow the app: null dark, 0-digit
dark, 1-digit bright, carry tinted, LeastEdge green.
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.collections import PatchCollection

import collatz_real as R


def cell_color(x):
    if x is None:
        return None                      # blank -> don't draw
    if R.isLE(x):
        return "#39d353"                 # LeastEdge = bright green
    d, c = x["d"], x["c"]
    if d and c:
        return "#c9a0ff"                 # 1 with carry
    if d:
        return "#7c3aed"                 # 1
    if c:
        return "#2a2240"                 # 0 with carry
    return "#1a1e24"                     # 0


def render_hex(grid, path, title="", cellsize=1.0, maxcols=None, maxrows=None,
               figscale=0.16):
    H = len(grid)
    W = len(grid[0])
    if maxrows:
        H = min(H, maxrows)
    if maxcols:
        W = min(W, maxcols)
    Rr = cellsize / 2.0
    sqrt3 = math.sqrt(3)
    hexW = sqrt3 * Rr
    patches, colors = [], []
    minx = miny = 1e9
    maxx = maxy = -1e9
    for r in range(H):
        cy = -r * 1.5 * Rr               # negative so row 0 on top
        for c in range(W):
            x = grid[r][c]
            col = cell_color(x)
            if col is None:
                continue
            dc = W - 1 - c               # MSB (high c) on the left
            cx = dc * hexW + r * hexW / 2.0
            patches.append(RegularPolygon((cx, cy), numVertices=6,
                                          radius=Rr * 0.98, orientation=0))
            colors.append(col)
            minx = min(minx, cx); maxx = max(maxx, cx)
            miny = min(miny, cy); maxy = max(maxy, cy)
    fig_w = max(6.0, (maxx - minx) * figscale)
    fig_h = max(4.0, (maxy - miny) * figscale)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=130)
    pc = PatchCollection(patches, facecolors=colors, edgecolors="#0b0b14",
                         linewidths=0.3)
    ax.add_collection(pc)
    ax.set_xlim(minx - 1, maxx + 1)
    ax.set_ylim(miny - 1, maxy + 1)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=12, color="#111")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    fig.savefig(path, facecolor="white", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import os
    g = R.run(27, 44, 34)
    out = os.path.join(os.path.dirname(__file__), os.pardir, "images",
                       "collatz-hex-27.png")
    render_hex(g, out, title="CA.CollatzStep, seed 27, hex view (MSB left, LeastEdge green)")
    print("wrote", out)
