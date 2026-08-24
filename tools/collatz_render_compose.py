#!/usr/bin/env python3
"""Hex renders for the composable-block results. SCOPE: [real-CA].
Every grid here is CA.CollatzStep run cell-by-cell (collatz_real.run) on an
integer tape built by collatz_compose; nothing comes from a proxy model.

  collatz-compose-zoo.png     solo blocks: word + right-edge motif + rhythm
  collatz-compose-wall.png    same pair, raw cut vs designed splice
  collatz-compose-triple.png  three blocks spliced: a rhythm program
"""
import os
import math
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.collections import PatchCollection

import collatz_real as R
import collatz_compose as C

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
HEXW = math.sqrt(3) * 0.5


def sea_front(vs):
    """Cumulative halvings per row: the LeastEdge front position."""
    S, out = 0, [0]
    for v in vs:
        S += v
        out.append(S)
    return out


def draw_grid(ax, grid, walls=(), notes=(), front=None):
    """walls: tape bit positions (bold pink line, drawn to just past the sea
    crossing).  notes: (row, text, color) placed just right of the sea front.
    front: sea_front list, needed for walls/notes."""
    H, W = len(grid), len(grid[0])
    patches, colors = [], []
    for r in range(H):
        cy = -r * 0.75
        for c in range(W):
            x = grid[r][c]
            col = None if x is None else (
                "#39d353" if R.isLE(x) else
                "#c9a0ff" if x["d"] and x["c"] else
                "#7c3aed" if x["d"] else
                "#2a2240" if x["c"] else "#1a1e24")
            if col is None:
                continue
            dc = W - 1 - c
            patches.append(RegularPolygon(
                (dc * HEXW + r * HEXW / 2.0, cy), numVertices=6,
                radius=0.49, orientation=0))
            colors.append(col)
    ax.add_collection(PatchCollection(patches, facecolors=colors,
                                      edgecolors="#0b0b14", linewidths=0.25))
    for wb in walls:
        cross = next((i for i, s in enumerate(front) if s >= wb), H - 1)
        rr = range(0, min(H, cross + 6))
        ax.plot([(W - 1 - (wb + 1)) * HEXW + r * HEXW / 2.0 for r in rr],
                [-r * 0.75 for r in rr], color="#ff2d6f", lw=2.2, alpha=0.95)
    for row, text, colr in notes:
        row = min(row, H - 1)
        x = (W - 1 - front[row]) * HEXW + row * HEXW / 2.0
        ax.text(x + 4, -row * 0.75, text, color=colr, fontsize=9.5,
                va="center", fontweight="bold",
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="none",
                          pad=1.5))
    ax.set_xlim(-1, (W - 1) * HEXW + H * HEXW / 2.0 + 1)
    ax.set_ylim(-(H - 1) * 0.75 - 1, 1)
    ax.set_aspect("equal")
    ax.axis("off")


def grid_of(n, steps):
    W = n.bit_length() + 2 * steps + 6
    return R.run(n, W, steps + 1)


def panel_fig(grids, captions, suptitle, out, all_walls, all_notes, fronts,
              scale=0.055):
    Ws = [len(g[0]) + len(g) / 2 for g in grids]
    Hs = [len(g) * 0.75 for g in grids]
    fw = max(Ws) * HEXW * scale + 1
    fh = sum(h * scale + 1.0 for h in Hs) + 0.9
    fh = sum(h * scale + 1.5 for h in Hs) + 0.9
    fig, axes = plt.subplots(len(grids), 1, figsize=(fw, fh), dpi=150,
                             gridspec_kw=dict(height_ratios=[h + 20 for h in Hs]))
    if len(grids) == 1:
        axes = [axes]
    for ax, g, cap, walls, notes, front in zip(axes, grids, captions,
                                               all_walls, all_notes, fronts):
        draw_grid(ax, g, walls=walls, notes=notes, front=front)
        ax.set_title("\n".join(textwrap.wrap(cap, 110)), fontsize=10,
                     loc="left", pad=14)
    fig.suptitle(suptitle, fontsize=11.5)
    fig.tight_layout(rect=[0, 0, 1, 1 - 0.55 / fh * suptitle.count("\n")])
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def fig_zoo(blocks):
    picks = [("d1  (the fuse)", 1, 30, 16), ("d11", 11, None, None),
             ("d49", 49, None, None), ("d31", 31, None, None),
             ("d217", 217, None, None)]
    grids, caps, fronts = [], [], []
    for label, den, Mo, Ho in picks:
        b = next(x for x in blocks
                 if x.den == den and (den != 1 or x.x == -1))
        copies = {1: 30, 11: 5, 49: 3, 31: 8, 217: 4}[den]
        M = Mo or (b.q * copies + len(b.pre))
        n = C.expansion(b.x, M)
        H = Ho or min(int((M - len(b.pre)) / b.vbar) - b.l, 4 * b.l + 3)
        rows, vs = C.run_int(n, H)
        grids.append(grid_of(n, H))
        fronts.append(sea_front(vs))
        caps.append("%s   word period %d, density %.2f, right-edge motif "
                    "\"%s\", rhythm v=%s: eats %.2f cells/step, MSB grows "
                    "+1.585, net %+.2f bits/step"
                    % (label, b.q, b.dens, b.pre or "none",
                       ",".join(map(str, b.vs)), b.vbar, b.growth))
    panel_fig(grids, caps,
              "[real-CA] the block zoo: five growing blocks run in "
              "CA.CollatzStep (MSB left, LeastEdge green).\nEach block = "
              "repeating word + right-edge motif + locked halving rhythm; "
              "each eats slower than the generic 2 cells/step, so each "
              "spreads left.",
              os.path.join(IMG, "collatz-compose-zoo.png"),
              [[]] * 5, [[]] * 5, fronts)


def fig_wall(blocks):
    a = next(x for x in blocks if x.den == 11)
    b = next(x for x in blocks if x.den == 49)
    MB = b.q * 2 + len(b.pre) + 4      # a decisively scrambling cut phase
    n_raw = (C.tail_int(a, 5 * a.q) << MB) | C.expansion(b.x, MB)
    H = int(MB / b.vbar) + 26
    rows_r, vs_r = C.run_int(n_raw, H)
    g_raw = grid_of(n_raw, H)
    fr_r = sea_front(vs_r)
    cross_r = next(i for i, s in enumerate(fr_r) if s >= MB)

    per = max(1, round(MB / b.S))
    n_sp, S, agree = C.splice(a, b, periods=per, adepth=5 * a.q + 8)
    rows_s, vs_s = C.run_int(n_sp, H)
    g_sp = grid_of(n_sp, H)
    fr_s = sea_front(vs_s)
    cross_s = next(i for i, s in enumerate(fr_s) if s >= S)

    import statistics
    post_mean = statistics.mean(vs_r[cross_r:cross_r + 40])
    cap_raw = ("RAW CUT: five d11 words butted straight onto two d49 words "
               "(wall = pink line). B's rhythm is exact up to the wall; the "
               "cut digits then throw the orbit out of every cycle basin: "
               "the rhythm scrambles (mean eating %.2f cells/step over the "
               "next 40) and both identities die. Measured v after the "
               "wall: %s..."
               % (post_mean,
                  ",".join(map(str, vs_r[cross_r:cross_r + 12]))))
    cap_sp = ("DESIGNED SPLICE: same two blocks, but the tape is the exact "
              "preimage of d11's cycle under %d periods of d49's rhythm. "
              "The runner law forces the low %d digits to be d49's own word "
              "(digit agreement %d): B is untouched, and d11's rhythm locks "
              "with ZERO transient. Measured v after the wall: %s..."
              % (per, S, agree,
                 ",".join(map(str, vs_s[cross_s:cross_s + 12]))))
    notes_r = [(max(2, cross_r // 2), "d49 rhythm 1,1,1,2", "#0a6b28"),
               (min(H - 2, cross_r + 10), "scrambled: generic decay",
                "#b00040")]
    notes_s = [(max(2, cross_s // 2), "d49 rhythm 1,1,1,2", "#0a6b28"),
               (min(H - 2, cross_s + 10), "d11 rhythm 1,1,2 locks at once",
                "#5b3fa8")]
    panel_fig([g_raw, g_sp], [cap_raw, cap_sp],
              "[real-CA] the composition law, one pair both ways: "
              "A = d11 (word q=10, v=1,1,2) over B = d49 (word q=21, "
              "v=1,1,1,2).\nWhether the pattern survives the wall is decided "
              "by ONE thing: whether the wall's 2-adic value lies in A's "
              "cycle basin. Raw cuts almost never do; the computed wall "
              "always does (0/360 exceptions).",
              os.path.join(IMG, "collatz-compose-wall.png"),
              [[MB], [S]], [notes_r, notes_s], [fr_r, fr_s])


def fig_triple(blocks):
    top = next(x for x in blocks if x.den == 31)
    mid = next(x for x in blocks if x.den == 49)
    bot = next(x for x in blocks if x.den == 11)
    P_BOT, P_MID, P_TOP = 8, 5, 5
    z = top.x
    for v in reversed(list(mid.vs) * P_MID):
        z = (z * 2**v - 1) / 3
    for v in reversed(list(bot.vs) * P_BOT):
        z = (z * 2**v - 1) / 3
    S1 = P_BOT * bot.S
    S2 = S1 + P_MID * mid.S
    n = C.expansion(z, S2 + 8 * top.q + 10)
    steps = P_BOT * bot.l + P_MID * mid.l + P_TOP * top.l
    rows, vs = C.run_int(n, steps)
    want = list(bot.vs) * P_BOT + list(mid.vs) * P_MID
    okBM = vs[:len(want)] == want
    lock = C.rhythm_lock(vs[len(want):], list(top.vs))
    g = grid_of(n, steps)
    front = sea_front(vs)
    r1 = P_BOT * bot.l
    r2 = r1 + P_MID * mid.l
    notes = [(r1 // 2, "d11: v=1,1,2", "#5b3fa8"),
             ((r1 + r2) // 2, "d49: v=1,1,1,2", "#0a6b28"),
             (r2 + (steps - r2) // 2, "d31: v=1,1,1,1,1,4", "#b00040")]
    cap = ("Three spliced blocks, run as one integer: d11 words for %d "
           "steps, then d49 words for %d, then d31 words for %d. Both walls "
           "computed by preimage; measured rhythm sections exact = %s, top "
           "rhythm locked %d/%d steps. Note the sea's slope changing at "
           "each wall, and the upper zones sitting 'dressed' (x3-preimage "
           "texture) until their turn." % (r1, r2 - r1, steps - r2, okBM,
                                           lock, steps - r2))
    panel_fig([g], [cap],
              "[real-CA] a three-block program with designed walls: the tape "
              "as a rhythm score, zero transient at both handoffs.",
              os.path.join(IMG, "collatz-compose-triple.png"),
              [[S1, S2]], [notes], [front])
    print("triple: sections exact:", okBM, "top lock: %d/%d" % (lock, steps - r2))


def main():
    blocks = C.enumerate_blocks(7)
    fig_zoo(blocks)
    fig_wall(blocks)
    fig_triple(blocks)


if __name__ == "__main__":
    main()
