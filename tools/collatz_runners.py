#!/usr/bin/env /usr/bin/python3
"""Runner rhythm / fuse search: lifting construction, overshoot distribution,
and the exact 2-adic fuse law.

SCOPE: [value] = rows of the real CA (CA.CollatzStep); each row IS one odd step
n -> (3n+1)/2^v, and the v-sequence is the rhythm of the LeastEdge interface
(Lou's "runners"). The hex figure is [real-CA]. Nothing here uses x3-bulk or
ring windows.

WHAT IT DOES
1. Lifting construction: for any periodic v-pattern p the seeds sustaining the
   exact v-prefix (v1..vk), sum S, are ONE residue class mod 2^(S+1) (verified
   by brute-force census mod 2^14: census count == 2^(14-S-1) exactly, and
   mod 2^S is NOT enough - two classes survive there). The class is constructed
   two independent ways that agree bit-for-bit:
     (a) bitwise lifting (filter candidates by class-determined v-prefix),
     (b) the 2-adic expansion of the rational runner n* = C/(2^S - 3^l),
         C = sum_j 3^(l-1-j) 2^(v1+..+vj)   (period l, period-sum S).
   Anchors: p=(1) -> n* = -1 (all-ones tape); (1,2) -> -5; (2,1) -> -7; (2) -> 1.
   Refinement of the known anchor: n = -1 mod 2^k sustains v=1 for k-1 exact
   steps (the k-th needs one more bit); depth-K design costs K+1 bits.

2. EXACT FUSE LAW (the main find, verified on every trial, zero exceptions):
   let A = nu_2(n - n*) = number of low bits in which the tape agrees with the
   2-adic runner. Then the rhythm runs EXACTLY
       D(A) = min{ j : S_j + v_{j+1} >= A }   steps,   S_D(A) halvings,
   where S_j = v1+..+vj. Overshoot is deterministic, not luck: the "cooperating
   carry bits" above the designed region cooperate precisely when they equal
   the runner's 2-adic digits, bit for bit. (Proof sketch: n_j - n*_j =
   3^j 2^(A-S_j) u, u odd; valuation of 3n_j+1 is exactly v_{j+1} while
   A-S_j > v_{j+1}, and the break at S_j+v_{j+1} >= A is forced.)

3. Overshoot distribution (64-bit tapes, design 40 bits, 24 free high bits;
   96-bit tapes, design 64 bits, 32 free bits; N=40000 random phases per
   pattern per size, 8 patterns): law violations 0 / 640000. Excess agreement
   bits A-m follow the fair-coin geometric law P(A-m >= j) = 2^-j out to the
   sample floor: mean 0.99-1.02, P>=1 = .492-.511, P>=5 = .030-.033,
   P>=10 = .001, max over 40000 phases 14-19 bits =~ log2(N) + tail, for every
   pattern alike (all-ones runner and 5/7-runner identical). No pattern, phase,
   or tape structure beats it: the far tail is exactly the tapes whose free
   high bits copy the runner's 2-adic expansion; each copied bit buys one bit
   of halving budget.

   Fuse economics per pattern (64-bit tape, m=40): designed steps D = D(m),
   halvings H = S_D; e.g. (1): D=39 H=39; (2): D=19 H=38; (1,2): D=26 H=39;
   (1,1,2): D=29 H=38; (1,1,1,2): D=31 H=38. Value grows iff mean(v) < log2(3):
   (1),(1,2),(2,1),(1,1,2),(1,1,1,2) grow; (2),(1,3),(3,1) shrink.

Best finds (run of 2026-08-21, rng seed 20260821): 64-bit: pattern (2,1),
n = 14699749183737298937 = 0xcbfffffffffffff9, excess 18 (A=58): ran 38 steps
/ 57 halvings against designed 26 steps - its free high bits happen to
continue the runner -7 = ...111001 with 18 more ones (rendered in
images/collatz-runners-hex.png). 96-bit: (1,1,2) n =
50640363950795488418582995687 and (3,1) n = 46788883292856476573056743133,
both excess 19. Honest negative: nothing anomalous exists beyond geometric
luck; the "lucky" tapes are exactly prefixes of the runner's 2-adic expansion,
so no tape structure self-sustains its rhythm past its own information.

Run:  /usr/bin/python3 tools/collatz_runners.py         (full, ~1 min, 16 cores)
      /usr/bin/python3 tools/collatz_runners.py quick   (small N smoke test)
Outputs: printed tables, raw npz in /var/tmp/collatz-scratch/agentA/,
figures images/collatz-runners-dist.png and images/collatz-runners-hex.png.
"""

import math
import os
import random
import sys
from fractions import Fraction
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collatz_real as CR

SCRATCH = '/var/tmp/collatz-scratch/agentA'
IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'images')
PATTERNS = [(1,), (2,), (1, 2), (2, 1), (1, 1, 2), (1, 1, 1, 2), (1, 3), (3, 1)]
BIG = 1 << 256


def val2(x):
    return (x & -x).bit_length() - 1


def sustain(n, pat, cap=4000):
    """Run the odd map while the v-sequence follows pat cyclically.
    Returns (steps, halvings, final n)."""
    s = hv = 0
    l = len(pat)
    while s < cap:
        t = 3 * n + 1
        v = val2(t)
        if v != pat[s % l]:
            return s, hv, n
        n = t >> v
        hv += v
        s += 1
    return s, hv, n


def runner_rational(pat):
    """The 2-adic fixed point of one pattern period: n* = C/(2^S - 3^l)."""
    l, S = len(pat), sum(pat)
    C = 0
    V = 0
    for j in range(l):
        C += 3 ** (l - 1 - j) * (1 << V)
        V += pat[j]
    return C, (1 << S) - 3 ** l


def runner_bits(pat, bits):
    """Low `bits` 2-adic digits of the runner (the perfect tape)."""
    C, q = runner_rational(pat)
    M = 1 << bits
    return (C * pow(q, -1, M)) % M


def designed_profile(pat, A):
    """Exact fuse law: agreement A bits buys D steps and S_D halvings."""
    S = j = 0
    while True:
        v = pat[j % len(pat)]
        if S + v >= A:
            return j, S
        S += v
        j += 1


# ---------------------------------------------------------------- part 1: lift

def vseq_of_class(r, m, pat):
    """v-values determined by the residue class r mod 2^m (shrinking-modulus
    simulation). Returns (consistent_with_pat, steps_determined, halvings)."""
    n = r % (1 << m)
    rem, j, hv = m, 0, 0
    while True:
        t = 3 * n + 1
        v = val2(t)
        if v >= rem:
            return True, j, hv          # beyond here the class does not decide
        if v != pat[j % len(pat)]:
            return False, j, hv
        rem -= v
        n = (t >> v) % (1 << rem)
        hv += v
        j += 1


def lift(pat, m):
    """Bitwise lifting: the residue class mod 2^m sustaining pat deepest.
    Independent of runner_bits; used to cross-check it."""
    cands = [1]
    for M in range(2, m + 1):
        cands = [r for c in cands for r in (c, c + (1 << (M - 1)))
                 if vseq_of_class(r, M, pat)[0]]
        assert cands, (pat, M)
    return max(cands, key=lambda r: vseq_of_class(r, m, pat)[1])


def verify_lifting(report):
    report('== part 1: lifting construction [value] ==')
    # (a) bitwise lift == 2-adic runner expansion, per pattern, to 64 bits
    for pat in PATTERNS:
        r_lift = lift(pat, 64)
        r_run = runner_bits(pat, 64)
        C, q = runner_rational(pat)
        ok, D, H = vseq_of_class(r_run, 64, pat)
        assert r_lift == r_run, (pat, hex(r_lift), hex(r_run))
        report('  %-12s runner n* = %6s   class mod 2^64 = 0x%016x  '
               'designed D=%2d steps H=%2d halvings' %
               (pat, Fraction(C, q), r_run, D, H))
    # (b) brute-force census mod 2^14: seeds with exact v-prefix = ONE class
    #     mod 2^(S+1); mod 2^S leaves TWO classes (last valuation not pinned).
    Mc = 14
    for pat in [(1,), (1, 2), (1, 1, 2), (2, 1)]:
        k = 4 if sum(pat) * 4 // len(pat) < Mc - 2 else 2
        want = [pat[j % len(pat)] for j in range(k)]
        S = sum(want)
        hits = []
        for n in range(1, 1 << Mc, 2):
            seq = []
            x = n
            for _ in range(k):
                t = 3 * x + 1
                v = val2(t)
                seq.append(v)
                x = t >> v
            if seq == want:
                hits.append(n)
        cls = set(h % (1 << (S + 1)) for h in hits)
        assert len(cls) == 1 and len(hits) == 1 << (Mc - S - 1), (pat, len(cls))
        # the containing class mod 2^S does NOT suffice: only half its members
        # carry the prefix (2^S pins valuations >=, 2^(S+1) pins them exactly)
        in_classS = 1 << (Mc - S)
        report('  census mod 2^%d: prefix %s (S=%d): %d seeds = exactly one '
               'class mod 2^%d; its class mod 2^%d holds %d seeds, only half '
               'sustain' % (Mc, want, S, len(hits), S + 1, S, in_classS))
    # (c) the anchor, refined
    for k in (8, 16, 32):
        s, hv, _ = sustain((1 << k) - 1, (1,))
        report('  anchor: n = 2^%d - 1 sustains v=1 for %d exact steps '
               '(k-1, the k-th valuation needs one more bit)' % (k, s))
    report('')


# ------------------------------------------------------- part 2/3: experiment

def _chunk(args):
    pat, m, B, hs = args
    Rb = runner_bits(pat, 256)
    r = Rb % (1 << m)
    out = []
    for h in hs:
        n = r + (h << m)
        s, hv, _ = sustain(n, pat)
        d = (n - Rb) % BIG
        A = 256 if d == 0 else val2(d)
        out.append((s, hv, A, h))
    return pat, B, out


def experiment(N, report, rngseed=20260821):
    """Overshoot distribution over N random phases per (pattern, tape size)."""
    rng = random.Random(rngseed)
    jobs = []
    NCHUNK = 16
    for pat in PATTERNS:
        for (B, m) in [(64, 40), (96, 64)]:
            free = B - m
            hs = [rng.randrange(1 << (free - 1), 1 << free) for _ in range(N)]
            step = (N + NCHUNK - 1) // NCHUNK
            for i in range(0, N, step):
                jobs.append((pat, m, B, hs[i:i + step]))
    with Pool(16) as pool:
        parts = pool.map(_chunk, jobs)
    results = {}
    for pat, B, out in parts:
        results.setdefault((pat, B), []).extend(out)

    report('== part 2/3: fuse + overshoot, N=%d phases per pattern/size ==' % N)
    report('  tape B bits, design m bits (residue class), free = B-m high bits')
    report('  overshoot measured in excess agreement bits A-m; law: steps and')
    report('  halvings are EXACTLY designed_profile(pat, A)')
    header = ('  %-12s %3s/%2s | D0  H0 grow | mean  P>=1  P>=5 P>=10  max | '
              'law-viol' % ('pattern', 'B', 'm'))
    report(header)
    viol_total = 0
    best = {}
    for (pat, B), rows in sorted(results.items(), key=lambda kv: (kv[0][1], PATTERNS.index(kv[0][0]))):
        m = 40 if B == 64 else 64
        D0, H0 = designed_profile(pat, m)
        ex = [A - m for (_, _, A, _) in rows]
        viol = sum(1 for (s, hv, A, _) in rows
                   if (s, hv) != designed_profile(pat, A))
        viol_total += viol
        n_ = len(rows)
        mean = sum(ex) / n_
        p = lambda j: sum(1 for e in ex if e >= j) / n_
        mx = max(ex)
        grow = 'x%.2f/step' % (3 / 2 ** (sum(pat) / len(pat)))
        report('  %-12s %3d/%2d | %2d %3d %10s | %.2f %.3f %.3f %.3f  %3d | %d'
               % (pat, B, m, D0, H0, grow, mean, p(1), p(5), p(10), mx, viol))
        i = max(range(n_), key=lambda i: rows[i][2])
        s, hv, A, h = rows[i]
        r = runner_bits(pat, 256) % (1 << m)
        best[(pat, B)] = (r + (h << m), s, hv, A)
    report('  total law violations: %d / %d  (the fuse law is exact)'
           % (viol_total, sum(len(v) for v in results.values())))
    report('')
    report('  best finds (far tail = tapes copying the runner 2-adic digits):')
    for (pat, B), (n, s, hv, A) in sorted(best.items(),
                                          key=lambda kv: -(kv[1][3] - (40 if kv[0][1] == 64 else 64))):
        m = 40 if B == 64 else 64
        report('    %-12s B=%2d n=%d  ran %2d steps %2d halvings, '
               'A=%d (excess %d): high bits copy runner digits' %
               (pat, B, n, s, hv, A, A - m))
    report('')
    return results, best


# ------------------------------------------------------------------- figures

def fig_distribution(results, path):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    SURF, INK, INK2, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#898781', '#e1e0d9'
    # validated categorical palette (dataviz reference, light mode, fixed slot order)
    colors = ['#2a78d6', '#1baf7a', '#eda100', '#008300',
              '#4a3aa7', '#e34948', '#e87ba4', '#eb6834']
    markers = ['o', 's', '^', 'D', 'v', 'P', 'X', '*']
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=140)
    fig.patch.set_facecolor(SURF)
    for a in axes:
        a.set_facecolor(SURF)
        for sp in a.spines.values():
            sp.set_color(GRID)
        a.tick_params(colors=MUTED, labelsize=8)
    ax = axes[0]
    for i, pat in enumerate(PATTERNS):
        rows = results[(pat, 64)]
        ex = np.array([A - 40 for (_, _, A, _) in rows])
        n = len(ex)
        js = np.arange(0, ex.max() + 1)
        surv = np.array([(ex >= j).sum() / n for j in js])
        ax.semilogy(js, surv, '-', lw=1.6, color=colors[i],
                    marker=markers[i], ms=3.5, label='%s' % (pat,))
    jref = np.arange(0, 18)
    ax.semilogy(jref, 0.5 ** jref, ls='--', color=INK, lw=1,
                label=r'$2^{-j}$ (fair coin)')
    ax.set_xlabel('overshoot j = excess agreement bits beyond the 40-bit design',
                  color=INK2, fontsize=9)
    ax.set_ylabel(r'P(overshoot $\geq$ j)', color=INK2, fontsize=9)
    ax.set_title('overshoot survival, 64-bit tapes, N=%d phases/pattern:\n'
                 'all 8 rhythms collapse onto the fair-coin geometric law'
                 % len(results[((1,), 64)]), fontsize=10, color=INK)
    ax.legend(fontsize=7.5, ncol=2, frameon=False, labelcolor=INK2)
    ax.grid(True, which='both', color=GRID, lw=0.5)

    ax = axes[1]
    allA, allhv, allpred = [], [], []
    for (pat, B), rows in results.items():
        for (s, hv, A, _) in rows[::40]:
            allA.append(A)
            allhv.append(hv)
            allpred.append(designed_profile(pat, A)[1])
    allA, allhv, allpred = map(np.array, (allA, allhv, allpred))
    ax.plot(allA, allA, '-', color=GRID, lw=1.2, label='halvings = A (ceiling)')
    ax.scatter(allA, allhv, s=7, color='#2a78d6', alpha=0.45, lw=0,
               label='measured halvings (all patterns, both sizes)')
    assert (allhv == allpred).all()
    ax.set_xlabel(r'A = 2-adic agreement bits with the runner $n^*$',
                  color=INK2, fontsize=9)
    ax.set_ylabel('halvings actually sustained', color=INK2, fontsize=9)
    ax.set_title('the exact fuse law: halvings = $S_{D(A)}$, no exceptions\n'
                 '(A bits of runner agreement buy A-O(1) halvings, then stop)',
                 fontsize=10, color=INK)
    ax.legend(fontsize=8, frameon=False, labelcolor=INK2)
    ax.grid(True, color=GRID, lw=0.5)
    fig.suptitle('[value] runner rhythms as fuses: overshoot beyond the designed '
                 'region is exactly 2-adic agreement with the rational runner',
                 fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, facecolor='white', bbox_inches='tight')
    print('wrote', path)


def fig_hex(n, pat, A, m, path):
    """Hex render of the best fuse running in the REAL automaton."""
    import collatz_hex as HX
    D, H = designed_profile(pat, A)
    rows = D + 6
    # trajectory to size the grid
    traj = [n]
    x = n
    for _ in range(rows):
        t = 3 * x + 1
        while t % 2 == 0:
            t //= 2
        traj.append(t)
        x = t
    hv = 0
    width = n.bit_length() + 2
    x = n
    for j in range(rows):
        t = 3 * x + 1
        v = val2(t)
        hv += v
        x = t >> v
        width = max(width, hv + x.bit_length() + 2)
    g = CR.run(n, width, rows + 1)
    got = [CR.readrow(g, r) for r in range(rows + 1)]
    assert got == traj[:rows + 1], 'real-CA trajectory mismatch'
    D0, H0 = designed_profile(pat, m)
    title = ('[real-CA] CA.CollatzStep hex view: best %d-bit fuse for rhythm %s, '
             'n=%d\ndesigned %d bits -> %d steps; free high bits copied %d extra '
             'runner digits -> ran %d steps / %d halvings, then broke '
             '(rows after the break are ordinary Collatz)'
             % (n.bit_length(), pat, n, m, D0, A - m, D, H))
    HX.render_hex(g, path, title=title, figscale=0.11)
    print('wrote', path)


def main():
    quick = len(sys.argv) > 1 and sys.argv[1] == 'quick'
    N = 2000 if quick else 40000
    os.makedirs(SCRATCH, exist_ok=True)
    lines = []

    def report(s):
        print(s)
        lines.append(s)

    # ground truth gate
    g = CR.run(27, 70, 46)
    rows = [CR.readrow(g, r) for r in range(7)]
    assert rows == [27, 41, 31, 47, 71, 107, 161], 'ground truth FAILED'
    report('[real-CA] ground truth verified: seed 27 rows %s...' % rows)
    report('')

    verify_lifting(report)
    results, best = experiment(N, report)

    # raw data for follow-up
    import numpy as np
    raw = {}
    for (pat, B), rws in results.items():
        key = 'p%s_B%d' % ('_'.join(map(str, pat)), B)
        raw[key] = np.array([(s, hv, A) for (s, hv, A, _) in rws], dtype=np.int64)
        raw[key + '_h'] = np.array([h for (_, _, _, h) in rws], dtype=np.int64)
    np.savez_compressed(os.path.join(SCRATCH, 'runners_raw.npz'), **raw)
    with open(os.path.join(SCRATCH, 'runners_report.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    report('raw data: %s/runners_raw.npz' % SCRATCH)

    fig_distribution(results, os.path.join(IMAGES, 'collatz-runners-dist.png'))
    # best 64-bit growth-pattern fuse for the hex render
    grow_pats = [p for p in PATTERNS if sum(p) / len(p) < math.log2(3)]
    (pat, B), (n, s, hv, A) = max(((k, v) for k, v in best.items()
                                   if k[0] in grow_pats and k[1] == 64),
                                  key=lambda kv: kv[1][3])
    fig_hex(n, pat, A, 40, os.path.join(IMAGES, 'collatz-runners-hex.png'))


if __name__ == '__main__':
    main()
