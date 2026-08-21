#!/usr/bin/env python3
"""[real-CA antidiagonal] Off-shell state space of the diagonalized CA.CollatzStep.

DERIVATION. In ca-collatz-step.js cell (r,c) depends on above=(r-1,c),
shifted=(r-1,c-1), and the same-row carry left=(r,c-1). With machine time
t = r + c the deltas are +1, +2, +1: all positive, so the antidiagonals
t = const are the true causal slices, and because of the delta-t=2 shifted
dep the machine state is TWO consecutive antidiagonals A(t-1), A(t).
Within one antidiagonal there are no dependencies, so
    A(t+1)[r] = rule( above=A(t)[r-1], shifted=A(t-1)[r-1], left=A(t)[r] )
for r>=1, and A(t+1)[0] = seed-row cell (0, t+1) = None once t+1 > msb.
Out-of-range indices are None (c<0 or r<0), matching this.get(). The rule
is the exact CollatzStep rule including both LeastEdge spreading clauses.
This is the same dependency DAG as the row-major loop, so on-shell the two
schedules agree cell-for-cell (VERIFIED, see below); off-shell there is no
row-major counterpart at all: the carry field on a slice is genuine state
and can be set to values no integer history produces.

Cell encoding (int8): 0=None, 1=(d0,c0), 2=(d1,c0), 3=(d0,c1), 4=(d1,c1),
5=LeastEdge (digit 0, carry 1, per CA.LEAST_EDGE in ca-base.js).

VERIFICATION [real-CA]: antidiagonal evolution initialized from two slices
of a tools/collatz_real.py grid reproduces that grid EXACTLY on every
comparable interior cell: seed 27 (70x46) at t0=6 and t0=40 (0/3129 and
0/2330 mismatches) and a fixed 192-bit odd seed (480x200) at t0=msb+1 and
mid-band t0 (0/76799 and 0/61093). An encoded row-major re-port (step_row)
also matches collatz_real cell-for-cell. Off-shell results cannot be
scheduling artifacts: the slice update solves the same local equations,
and given the two initial slices the solution grid is unique.

FINDINGS (sweep: 1048 single/double-cell perturbations across 4 slice
pairs of a 192-bit run, horizon 400 slices, 16 procs; plus long-horizon
T=1400 runs; classification by strict slice-equality vs the reference
evolution and by per-row trajectory-link checking n_{r+1}=odd(n_r) with
matching LE-front advance):
1. CARRY IS REAL BUT EPHEMERAL STATE. A cell's carry is read only by its
   same-row neighbor, which lies on the NEXT slice: so on a slice pair the
   older slice's carries are already spent - all 50 carry flips on the
   older slice changed nothing, ever (exact no-ops). Off-shell carry
   information lives for exactly one slice.
2. THE SHELL IS AN IMMEDIATE ATTRACTOR. Every carry flip (240) and digit
   flip (240) on the newer slice produced exactly ONE broken trajectory
   link and healed in 0 rows: the first complete row after the flip is
   already a perfect integer seed and everything below is the on-shell
   history of that different integer. Double carry flips: same, heal <=7
   rows. There is no off-shell diffusion at all - a perturbation is
   instantly reinterpreted as a different number.
3. ~8% of flips (42/480, all in low-bit cells near the LeastEdge front)
   relaxed back to the REFERENCE exactly, carries included. Mechanism:
   value-map coalescence, seen spatially - the flip re-seeds a nearby
   integer whose Collatz orbit merges with the host's within ~100 rows;
   the difference region is a closed wedge (e.g. rows 78..159), then the
   two futures are cell-identical.
4. The deep LeastEdge region is DEAD STATE: replacing interior LE cells by
   any digit/carry code changed no future cell in 81/96 cases (the LE
   column above forces LE and regenerates); near-front replacements heal
   or re-seed (front bookkeeping = halvings change the value).
5. Mid-band LE insertion cuts the number in two: the insertion becomes a
   permanent LE column; the low-c fragment is a capped machine (its MSB
   growth is absorbed by the column, and >=1 halving/row shrinks it) that
   ALWAYS burned out (240/240 within horizon, heal 1..99 rows ~ fragment
   size); the high-c fragment continues as a genuine on-shell trajectory
   of its own value, which then owns the tape.
6. Digit seeds in the void beyond the MSB become GHOST NUMBERS running the
   pure x3 automaton (no LeastEdge -> no +1, no halving): x3-bulk dynamics
   embedded in the real CA. Transient: the host MSB advances ~log2(3)
   cols/row into the ghost's fixed LSB column and absorbs it by addition
   (68/68 healed, 3..132 rows), after which the tape is on-shell again.
7. A LeastEdge cell in the void BOOTS A SECOND MACHINE: its carry emits a
   1 into the empty cell to its right, reproducing initGrid(1) - a
   self-sustaining 1-cycle engine (front speed 2 cols/row). Two disjoint
   machines on one tape is off-shell (no integer history has two fronts).
   But it is NOT persistent: the boot column is a permanent LE wall that
   caps the host's MSB growth; the host is consumed like the fragment in
   (5), and the tape relaxes to the n=1 shell of the parasite (confirmed
   to depth 80 cols with T=1400: all relax, heal ~100-134 rows; the
   at-horizon "second front" cases of the short sweep were this, unfinished).
CONCLUSION: the off-shell state space of the real CA is thin. Carries are
one-slice gauge freedom; every local perturbation lands on the shell of
SOME integer within ~2 rows; multi-machine sectors (extra LE fronts, x3
ghosts) are the only long-lived off-shell episodes and all end in a single
machine owning the tape (merge, burn-out, or parasite takeover). No
persistent bounded off-shell soliton was found; every lasting structure is
itself an on-shell machine.

Usage: --verify | --sweep | --render | --all
"""
import sys, os, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collatz_real as CR

NONE, D0, D1, D0C, D1C, LEC = 0, 1, 2, 3, 4, 5
DIG = np.array([0, 0, 1, 0, 1, 0], dtype=np.int8)   # digit of each code (LE d=0)
CAR = np.array([0, 0, 0, 1, 1, 1], dtype=np.int8)   # carry of each code (LE c=1)

def encode_cell(x):
    if x is None: return NONE
    if x.get('le'): return LEC
    return 1 + x['d'] + 2 * x['c']

def encode_grid(g):
    H, W = len(g), len(g[0])
    a = np.zeros((H, W), dtype=np.int8)
    for r in range(H):
        for c in range(W):
            a[r, c] = encode_cell(g[r][c])
    return a

# ---------------------------------------------------------------- rule kernels

def step_diag(prev, cur):
    """Advance one antidiagonal. prev=A(t-1) (len t), cur=A(t) (len t+1),
    indexed by row r (column is c=t-r). Returns A(t+1) (len t+2).
    A(t+1)[0] (seed-row cell) is None: only valid for t+1 > seed msb."""
    t = len(cur) - 1
    above   = cur                                          # r-1 = 0..t
    shifted = np.concatenate([prev, np.int8([NONE])])      # A(t-1)[r-1], r-1=t -> c=-1 None
    left    = np.concatenate([cur[1:], np.int8([NONE])])   # A(t)[r], r=t+1 -> c=-1 None
    carry_in = np.where(left == NONE, 0, CAR[left]).astype(np.int8)
    s = DIG[shifted] + DIG[above] + carry_in
    digit = s & 1
    carry = (s >= 2).astype(np.int8)
    out = (1 + digit + 2 * carry).astype(np.int8)
    out[(shifted == NONE) & (above == NONE) & (carry_in == 0)] = NONE
    above_d0 = (above == D0) | (above == D0C)
    out[(left == LEC) & (((digit == 0) & (carry == 1)) | (above_d0 & (shifted == LEC)))] = LEC
    out[above == LEC] = LEC                                # highest priority
    return np.concatenate([np.int8([NONE]), out])

def step_row(prev_row, W):
    """Row-major re-port on the encoding (independent check of the rule)."""
    out = np.zeros(W, dtype=np.int8)
    for c in range(W):
        above = prev_row[c]
        if above == LEC: out[c] = LEC; continue
        shifted = prev_row[c-1] if c > 0 else NONE
        left = out[c-1] if c > 0 else NONE
        ci = int(CAR[left]) if left != NONE else 0
        if shifted == NONE and above == NONE and ci == 0: out[c] = NONE; continue
        s = int(DIG[shifted]) + int(DIG[above]) + ci
        d, cy = s & 1, 1 if s >= 2 else 0
        if left == LEC and ((d == 0 and cy == 1) or
                            (above in (D0, D0C) and shifted == LEC)):
            out[c] = LEC; continue
        out[c] = 1 + d + 2 * cy
    return out

def ref_grid(n, H, W):
    """Encoded reference grid via the fast row stepper (verified == collatz_real)."""
    g = np.zeros((H, W), dtype=np.int8)
    msb = max(1, n.bit_length())
    g[0, 0] = LEC
    for c in range(1, W):
        g[0, c] = (1 + ((n >> (c-1)) & 1)) if (c-1) < msb else NONE
    for r in range(1, H):
        g[r] = step_row(g[r-1], W)
    return g

# ------------------------------------------------------- antidiagonal machine

def get_diag(G, t):
    """Extract A(t) from grid (rows 0..min(t,H-1); pads with NONE where c>=W)."""
    H, W = G.shape
    out = np.zeros(t + 1, dtype=np.int8)
    for r in range(min(t, H - 1) + 1):
        c = t - r
        out[r] = G[r, c] if c < W else NONE
    return out

def evolve(prev, cur, t0, T):
    """Run T antidiagonal steps from (A(t0-1), A(t0)). Requires t0 > seed msb
    so the r=0 boundary is None. Yields (t, A(t)) for t = t0+1 .. t0+T."""
    for k in range(T):
        nxt = step_diag(prev, cur)
        prev, cur = cur, nxt
        yield t0 + 1 + k, cur

def evolve_to_grid(prev, cur, t0, T, base=None):
    """Evolve and assemble a grid. Cells with r+c <= t0 come from `base`
    (reference grid) if given, else are left 0; cells with r+c in
    [t0-1, t0+T] come from the antidiagonal machine."""
    t_end = t0 + T
    H = t_end + 1
    W = t_end + 1
    G = np.zeros((H, W), dtype=np.int8)
    if base is not None:
        h = min(base.shape[0], H); w = min(base.shape[1], W)
        G[:h, :w] = base[:h, :w]
        # blank the beyond-horizon triangle r+c > t_end: those cells are
        # never computed and must not leak stale reference content
        rr, cc = np.indices((H, W), sparse=True)
        G[rr + cc > t_end] = NONE
    for arr, t in ((prev, t0 - 1), (cur, t0)):
        for r in range(len(arr)):
            if r < H and 0 <= t - r < W: G[r, t - r] = arr[r]
    for t, A in evolve(prev, cur, t0, T):
        rs = np.arange(len(A))
        cs = t - rs
        m = (rs < H) & (cs >= 0) & (cs < W)
        G[rs[m], cs[m]] = A[m]
    return G

# ----------------------------------------------------------------- analysis

def v2(x):
    return (x & -x).bit_length() - 1 if x else 0

def odd_step(n):
    m = 3 * n + 1
    return m >> v2(m), v2(m)

def parse_row(row):
    """-> dict: well_formed, n, f (LE front), segments, interior_le, fronts."""
    C = len(row)
    is_le = row == LEC
    is_dig = (row >= D0) & (row <= D1C)
    f = 0
    while f < C and row[f] == LEC: f += 1
    nz = np.flatnonzero(is_dig)
    segs = []
    if len(nz):
        brk = np.flatnonzero(np.diff(nz) > 1)
        starts = np.concatenate([[0], brk + 1]); ends = np.concatenate([brk, [len(nz)-1]])
        segs = [(int(nz[a]), int(nz[b])) for a, b in zip(starts, ends)]
    interior_le = int(is_le[f:].sum())            # LE cells after the prefix
    le_idx = np.flatnonzero(is_le)
    fronts = 1 + int(np.sum(np.diff(le_idx) > 1)) if len(le_idx) else 0
    wf = (fronts <= 1 and interior_le == 0 and len(segs) == 1
          and (len(le_idx) == 0 or le_idx[0] == 0)
          and (not segs or segs[0][0] == f))
    n = None
    if wf and segs:
        bits = DIG[row[segs[0][0]:segs[0][1]+1]]
        n = int(sum(int(b) << k for k, b in enumerate(bits)))
    return dict(well_formed=wf, n=n, f=f, segments=segs,
                interior_le=interior_le, fronts=fronts)

def row_complete(row, t, r, t_end):
    """Row r known up to c = t_end - r; complete if band ended before that."""
    c_max = t_end - r
    return c_max >= 2 and row[c_max] == NONE and row[c_max - 1] == NONE

def classify(G, t0, T, r0, ref_vals, last_diff_t=None):
    """Classify one perturbed run. r0 = first affected row.
    ref_vals[r] = reference integer of row r. last_diff_t = last slice at
    which the perturbed state differed from the reference evolution
    (None = never differed; strict relaxation to the reference if < t0+T)."""
    if last_diff_t is None or last_diff_t <= t0:
        # state was edited but no future slice ever differs: the edited
        # bits were dead state (e.g. any carry on the older slice)
        return dict(cls='no-op-dead-state', heal=0, detail='')
    if last_diff_t < t0 + T:
        return dict(cls='relax-to-reference', heal=None, detail='',
                    heal_slices=last_diff_t - t0)
    t_end = t0 + T
    H = G.shape[0]
    r_hi = r0
    info = {}
    for r in range(max(1, r0 - 1), H):
        if not row_complete(G[r], t0, r, t_end): break
        info[r] = parse_row(G[r])
        r_hi = r
    if r_hi <= r0 + 2:
        return dict(cls='horizon-too-short', heal=None, detail='')
    def consistent(r):
        if r not in info or r + 1 not in info: return False
        a, b = info[r], info[r + 1]
        if not (a['well_formed'] and b['well_formed']
                and a['n'] is not None and b['n'] is not None):
            return False
        nn, k = odd_step(a['n'])
        return b['n'] == nn and b['f'] == a['f'] + k
    ok = {r: consistent(r) for r in range(r0, r_hi)}
    r_star = None
    for r in range(r0, r_hi):
        if all(ok[q] for q in range(r, r_hi)):
            r_star = r; break
    last = info[r_hi]
    if r_star is not None:
        # count broken trajectory links, including the seam into row r0
        broken = sum(1 for r in range(max(1, r0 - 1), r_star) if not consistent(r))
        same = all(info[r]['n'] == ref_vals[r] for r in range(r_star, r_hi + 1)
                   if r < len(ref_vals))
        cls = 'relax-to-reference-values' if same else 'relax-to-new-shell'
        return dict(cls=cls, heal=r_star - r0, broken=broken,
                    detail=f'n[{r_hi}]={last["n"]}')
    d = f'fronts={last["fronts"]} segs={len(last["segments"])} intLE={last["interior_le"]}'
    if last['fronts'] >= 2:
        return dict(cls='not-healed-second-front@horizon', heal=None, detail=d)
    if len(last['segments']) >= 2:
        return dict(cls='not-healed-multiband@horizon', heal=None, detail=d)
    if last['interior_le'] > 0:
        return dict(cls='not-healed-interior-LE@horizon', heal=None, detail=d)
    return dict(cls='off-shell-unclassified', heal=None, detail=d)

# ------------------------------------------------------------- verification

SEED_BIG = (1 << 159) | 0x9e3779b97f4a7c15f39cc0605cedc8341082276bf3a27251  # odd, 192 bits

def verify_one(n, W, H, t0):
    g = CR.run(n, W, H)
    G = encode_grid(g)
    prev, cur = get_diag(G, t0 - 1), get_diag(G, t0)
    mism = 0; total = 0; first = None
    p, c = prev.copy(), cur.copy()
    for t, A in evolve(p, c, t0, W + H):
        for r in range(1, min(t, H - 1) + 1):
            col = t - r
            if col < W:
                total += 1
                if A[r] != G[r, col]:
                    mism += 1
                    if first is None: first = (r, col, int(G[r, col]), int(A[r]))
    return mism, total, first

def verify():
    ok = True
    # row-stepper vs collatz_real, seed 27
    G27 = encode_grid(CR.run(27, 70, 46))
    R27 = ref_grid(27, 46, 70)
    same = np.array_equal(G27, R27)
    print(f'[verify] step_row vs collatz_real seed 27: {"EXACT" if same else "MISMATCH"}')
    ok &= same
    msb = 27 .bit_length()
    for t0, label in ((msb + 1, 'seed-edge'), (40, 'mid-run')):
        m, tot, first = verify_one(27, 70, 46, t0)
        print(f'[verify] antidiag seed 27  t0={t0:3d} ({label}): '
              f'{m}/{tot} mismatches' + (f' first={first}' if first else ''))
        ok &= (m == 0)
    n = SEED_BIG
    msb = n.bit_length()
    W, H = 480, 200
    for t0, label in ((msb + 1, 'seed-edge'), (msb + 80, 'mid-run')):
        m, tot, first = verify_one(n, W, H, t0)
        print(f'[verify] antidiag 192-bit  t0={t0:3d} ({label}): '
              f'{m}/{tot} mismatches' + (f' first={first}' if first else ''))
        ok &= (m == 0)
    print(f'[verify] RESULT: {"ALL EXACT - antidiagonal machine == CA.CollatzStep" if ok else "FAILED"}')
    return ok

# ------------------------------------------------------------- perturbations

def make_context(n=SEED_BIG, r_mid=60, T=400):
    """Reference grid + a mid-run slice pair with a wide band crossing it."""
    msb = n.bit_length()
    traj = [n]; fronts = [1]
    for _ in range(2000):
        nn, k = odd_step(traj[-1]); traj.append(nn); fronts.append(fronts[-1] + k)
    t0 = max(msb + 2, r_mid + fronts[r_mid] + traj[r_mid].bit_length() // 2)
    assert t0 > msb + 1
    t_end = t0 + T
    H = t_end + 2; W = t_end + 2
    base = ref_grid(n, H, W)
    prev, cur = get_diag(base, t0 - 1), get_diag(base, t0)
    ref_vals = [None] * H
    for r in range(H):
        if r < len(traj): ref_vals[r] = traj[r]
    ref_hash = {}
    for t, A in evolve(prev.copy(), cur.copy(), t0, T):
        ref_hash[t] = A.tobytes()
    return dict(n=n, t0=t0, T=T, base=base, prev=prev, cur=cur,
                ref_vals=ref_vals, traj=traj, fronts=fronts, ref_hash=ref_hash)

CTX = None  # per-worker context

def _init_worker(n, r_mid, T):
    global CTX
    np.seterr(all='ignore')
    CTX = make_context(n, r_mid, T)

def run_pert(job):
    """job = (which, [(r, new_code), ...], tag). which: 'cur' or 'prev'."""
    which, edits, tag = job
    ctx = CTX
    prev, cur = ctx['prev'].copy(), ctx['cur'].copy()
    arr = cur if which == 'cur' else prev
    for r, code in edits:
        arr[r] = code
    t0, T = ctx['t0'], ctx['T']
    t_end = t0 + T
    H = W = t_end + 1
    G = np.zeros((H, W), dtype=np.int8)
    b = ctx['base']
    G[:min(b.shape[0], H), :min(b.shape[1], W)] = b[:H, :W]
    rr, cc = np.indices((H, W), sparse=True)
    G[rr + cc > t_end] = NONE   # never-computed triangle: no stale base cells
    for A, t in ((prev, t0 - 1), (cur, t0)):
        rs = np.arange(len(A)); cs = t - rs
        m = (rs < H) & (cs >= 0) & (cs < W)
        G[rs[m], cs[m]] = A[m]
    last_diff_t = t0 if not np.array_equal(cur, ctx['cur']) or \
                        not np.array_equal(prev, ctx['prev']) else None
    for t, A in evolve(prev, cur, t0, T):
        if A.tobytes() != ctx['ref_hash'][t]:
            last_diff_t = t
        rs = np.arange(len(A)); cs = t - rs
        m = (rs < H) & (cs >= 0) & (cs < W)
        G[rs[m], cs[m]] = A[m]
    r0 = max(1, min(r for r, _ in edits))
    res = classify(G, t0, T, r0, ctx['ref_vals'], last_diff_t)
    res.update(tag=tag, r=r0)
    return res

def build_jobs(ctx, rng):
    cur = ctx['cur']; prev = ctx['prev']
    is_dig = (cur >= D0) & (cur <= D1C)
    dig_rs = np.flatnonzero(is_dig)
    le_rs = np.flatnonzero(cur == LEC)
    none_rs = np.flatnonzero(cur == NONE)
    void_rs = none_rs[none_rs < dig_rs.min()] if len(dig_rs) else none_rs
    void_rs = void_rs[void_rs >= 1]
    jobs = []
    flip_c = {D0: D0C, D0C: D0, D1: D1C, D1C: D1}
    flip_d = {D0: D1, D1: D0, D0C: D1C, D1C: D0C}
    for r in dig_rs:
        r = int(r)
        jobs.append(('cur', [(r, flip_c[int(cur[r])])], 'carry-flip'))
        jobs.append(('cur', [(r, flip_d[int(cur[r])])], 'digit-flip'))
        jobs.append(('cur', [(r, LEC)], 'LE-insert-band'))
    # double carry flips (do off-shell defects interact?)
    for r in dig_rs[:-8:5]:
        r = int(r); r2 = int(r + 1 + rng.integers(1, 7))
        if cur[r2] in flip_c:
            jobs.append(('cur', [(r, flip_c[int(cur[r])]),
                                 (r2, flip_c[int(cur[r2])])], 'carry-flip-x2'))
    # perturbations of the OLDER slice: carries should be dead, digits not
    prev_dig = np.flatnonzero((prev >= D0) & (prev <= D1C))
    for r in prev_dig[::5]:
        r = int(r)
        jobs.append(('prev', [(r, flip_c[int(prev[r])])], 'carry-flip-prev'))
        jobs.append(('prev', [(r, flip_d[int(prev[r])])], 'digit-flip-prev'))
    # LE region: near the front and deep, all 4 digit codes
    front = int(le_rs.min()) if len(le_rs) else None
    if front is not None:
        picks = sorted(set([front, front + 1, front + 2, front + 5,
                            front + 10, front + 20]))
        for r in picks:
            if r < len(cur) and cur[r] == LEC:
                for code in (D0, D1, D0C, D1C):
                    jobs.append(('cur', [(r, code)], 'LE-delete'))
    # front shifts: extend the LE front by one
    if front is not None and front - 1 >= 1:
        jobs.append(('cur', [(front - 1, LEC)], 'front-extend'))
    # void seeds beyond the MSB (small r side), several depths
    if len(void_rs):
        vmax = int(void_rs.max())
        depths = sorted(set(max(1, vmax - d) for d in (2, 5, 10, 20, 40, 80)))
        for r in depths:
            if cur[r] == NONE:
                for code in (D1, D1C, D0C):
                    jobs.append(('cur', [(r, code)], 'void-digit'))
                jobs.append(('cur', [(r, LEC)], 'void-LE'))
                # a 2-cell void seed: a bigger ghost number
                if cur[r - 1] == NONE:
                    jobs.append(('cur', [(r, D1), (r - 1, D1)], 'void-digit-pair'))
    return jobs

def sweep(procs=16, r_mids=(30, 60, 90, 120), T=400):
    import multiprocessing as mp
    from collections import Counter, defaultdict
    rng = np.random.default_rng(1234)
    by = defaultdict(Counter)
    heals = defaultdict(list)
    details = defaultdict(list)
    total = 0
    for r_mid in r_mids:
        ctx = make_context(SEED_BIG, r_mid, T)
        jobs = build_jobs(ctx, rng)
        total += len(jobs)
        print(f'[sweep] 192-bit seed, slice pair at t0={ctx["t0"]} (band row ~{r_mid}), '
              f'horizon T={T} slices, {len(jobs)} perturbations, {procs} procs')
        with mp.Pool(procs, initializer=_init_worker,
                     initargs=(ctx['n'], r_mid, T)) as pool:
            results = pool.map(run_pert, jobs, chunksize=8)
        for res in results:
            by[res['tag']][res['cls']] += 1
            if res.get('heal') is not None and res['cls'].startswith('relax'):
                heals[(res['tag'], res['cls'])].append(res['heal'])
            if res['cls'].startswith('not-healed') or res['cls'] == 'off-shell-unclassified':
                details[res['tag']].append((res['r'], res['cls'], res['detail']))
            if res['tag'] in ('void-LE', 'LE-insert-band', 'void-digit') \
               and res['cls'] == 'relax-to-new-shell' and len(details[res['tag'] + ':sample']) < 3:
                details[res['tag'] + ':sample'].append(res['detail'][:70])
    print(f'\n[sweep] TOTAL {total} perturbations')
    print(f'{"perturbation":18s} {"outcome":32s} count   heal rows (min/med/max)')
    for tag in sorted(by):
        for cls, cnt in by[tag].most_common():
            h = sorted(heals[(tag, cls)])
            hs = (f'{h[0]}/{h[len(h)//2]}/{h[-1]}' if h else '')
            print(f'{tag:18s} {cls:32s} {cnt:5d}   {hs}')
    for tag, lst in sorted(details.items()):
        for item in lst[:6]:
            print(f'  [{tag}] {item}')
    return by

def longrun_voidle(procs=16):
    """Targeted long-horizon runs for the void-LE endgame: does the booted
    machine coexist with the host forever, or eat it?"""
    T = 1400
    ctx = make_context(SEED_BIG, 60, T)
    global CTX
    CTX = ctx
    cur = ctx['cur']
    dig_rs = np.flatnonzero((cur >= D0) & (cur <= D1C))
    void_rs = np.flatnonzero(cur == NONE)
    void_rs = void_rs[(void_rs >= 1) & (void_rs < dig_rs.min())]
    vmax = int(void_rs.max())
    for d in (5, 20, 40, 80):
        r = max(1, vmax - d)
        res = run_pert(('cur', [(r, LEC)], f'void-LE-d{d}'))
        print(f'[longrun] void-LE depth {d:3d} cols beyond MSB, T={T}: '
              f'{res["cls"]} heal={res.get("heal")} {res["detail"]}')

# --------------------------------------------------------------- rendering

PALETTE = {NONE: '#0d1117', D0: '#1a1e24', D0C: '#2a2240',
           D1: '#7c3aed', D1C: '#9455f5', LEC: '#3fb950'}

def render_panels(panels, fname, suptitle, cell=6):
    """panels: list of (title, G, (r0,r1,c0,c1)) crops. MSB LEFT: columns
    are reversed so high c (MSB side) is drawn on the left."""
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    cmap = ListedColormap([PALETTE[k] for k in range(6)])
    n = len(panels)
    fig, axes = plt.subplots(n, 1, figsize=(14, 4.2 * n), dpi=140)
    if n == 1: axes = [axes]
    for ax, (title, G, crop) in zip(axes, panels):
        r0, r1, c0, c1 = crop
        A = G[r0:r1, c0:c1][:, ::-1]           # MSB (high c) on the LEFT
        ax.imshow(A, cmap=cmap, vmin=0, vmax=5, interpolation='nearest',
                  aspect='equal',
                  extent=(c1 - 0.5, c0 - 0.5, r1 - 0.5, r0 - 0.5))
        ax.set_title(title, fontsize=9, loc='left')
        ax.set_ylabel('row', fontsize=8)
        ax.set_xlabel('column c (MSB left, LeastEdge/LSB side right)', fontsize=8)
        ax.tick_params(labelsize=7)
    leg = [Patch(fc=PALETTE[D0], label='0'), Patch(fc=PALETTE[D0C], label='0+'),
           Patch(fc=PALETTE[D1], label='1'), Patch(fc=PALETTE[D1C], label='1+'),
           Patch(fc=PALETTE[LEC], label='LeastEdge'), Patch(fc=PALETTE[NONE], label='void')]
    axes[0].legend(handles=leg, loc='upper right', fontsize=7, ncol=6,
                   framealpha=0.85)
    fig.suptitle(suptitle, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(fname, facecolor='white')
    plt.close(fig)
    print(f'[render] wrote {fname}')

def band_crop(G, r0, r1, pad=6):
    sub = G[r0:r1]
    nz = np.flatnonzero(sub.any(axis=0))
    c0 = max(0, int(nz.min()) - pad) if len(nz) else 0
    c1 = min(G.shape[1], int(nz.max()) + pad) if len(nz) else G.shape[1]
    return (r0, r1, c0, c1)

def render_all(outdir):
    ctx = make_context(T=400)
    t0, T, base = ctx['t0'], ctx['T'], ctx['base']
    cur0, prev0 = ctx['cur'], ctx['prev']
    is_dig = (cur0 >= D0) & (cur0 <= D1C)
    dig_rs = np.flatnonzero(is_dig)
    r_mid = int(dig_rs[len(dig_rs) // 2])
    G_ref = evolve_to_grid(prev0.copy(), cur0.copy(), t0, T, base=base)

    def perturbed(r, code):
        cur = cur0.copy(); cur[r] = code
        return evolve_to_grid(prev0.copy(), cur, t0, T, base=base)

    # 1. verification figure: reference vs antidiag reconstruction, seed 27
    G27 = encode_grid(CR.run(27, 70, 46))
    prev27, cur27 = get_diag(G27, 6), get_diag(G27, 7)
    R27 = evolve_to_grid(prev27, cur27, 7, 120, base=G27)[:46, :70]
    diff = (R27 != G27).astype(np.int8) * 4
    render_panels(
        [('row-major CA.CollatzStep (collatz_real.py), seed 27', G27, (0, 46, 0, 70)),
         ('antidiagonal machine, initialized from slices t=6,7 of that grid', R27, (0, 46, 0, 70)),
         (f'cellwise difference: {int((R27 != G27).sum())} mismatches', diff, (0, 46, 0, 70))],
        os.path.join(outdir, 'collatz-offshell-verify.png'),
        '[real-CA antidiagonal] VERIFICATION: antidiagonal (t=r+c) evolution == row-major CollatzStep, exactly')

    # 2. carry flip: one broken link then a new shell; plus a coalescing flip
    flip_c = {D0: D0C, D0C: D0, D1: D1C, D1C: D1}
    r = r_mid
    Gp = perturbed(r, flip_c[int(cur0[r])])
    dmask = (Gp != G_ref).astype(np.int8) * 4
    # a low-bit flip that coalesces back to the reference
    Gh, dh = None, None
    for r2 in dig_rs[::-1]:
        r2 = int(r2)
        cand = perturbed(r2, flip_c[int(cur0[r2])])
        dd = (cand != G_ref)
        rows = np.flatnonzero(dd.any(axis=1))
        if len(rows) and rows.max() < t0:  # difference wedge closed well before horizon
            Gh, dh, rh, rclose = cand, dd.astype(np.int8) * 4, r2, int(rows.max())
            break
    crop = band_crop(G_ref, max(0, r - 20), r + 140)
    panels = [
        ('reference on-shell history (192-bit seed)', G_ref, crop),
        (f'carry flipped at one cell of slice t={t0} (row {r}): exactly one broken trajectory link, then the\n'
         'perfect on-shell history of a DIFFERENT integer (heal = 0 rows)', Gp, crop),
        ('cells differing from reference: the flip is instantly reinterpreted as another number - no off-shell diffusion', dmask, crop)]
    if Gh is not None:
        panels.append((f'same flip at a low-bit cell (row {rh}): value-map COALESCENCE seen spatially - the re-seeded '
                       'integer merges\nback into the host orbit and the difference wedge closes (carries included, '
                       f'last differing row {rclose})',
                       dh, band_crop(G_ref, max(0, rh - 20), rclose + 25)))
    render_panels(panels,
        os.path.join(outdir, 'collatz-offshell-carryflip.png'),
        '[real-CA antidiagonal] off-shell carry flip: one broken link, instant relaxation onto the shell of another integer')

    # 3. mid-band LE insertion: cut the number in two
    Gc = perturbed(r_mid, LEC)
    crop = band_crop(Gc, max(0, r_mid - 20), r_mid + 280)
    render_panels(
        [('LeastEdge inserted mid-band: a permanent LE column cuts the number in two. The low half (right of the\n'
          'green column here; MSB drawn left) is a capped machine - MSB growth absorbed, >=1 halving/row - and burns\n'
          'out; the high half continues as the genuine on-shell Collatz trajectory of its own value and owns the tape', Gc, crop)],
        os.path.join(outdir, 'collatz-offshell-leinsert.png'),
        '[real-CA antidiagonal] mid-band LeastEdge insertion: the number is cut, the capped fragment burns out')

    # 4. void ghost (x3 dynamics) and void-booted second machine.
    # Use the deeper slice pair (band row ~120): its diagonal pokes ~230
    # columns beyond the MSB, leaving room to seed structures in the void.
    ctx2 = make_context(SEED_BIG, 120, 460)
    t02, T2 = ctx2['t0'], ctx2['T']
    cur2, prev2 = ctx2['cur'], ctx2['prev']
    dig2 = np.flatnonzero((cur2 >= D0) & (cur2 <= D1C))
    rv = int(dig2.min()) - 25          # 25 rows above the band on the slice
    assert rv >= 1 and cur2[rv] == NONE
    c0 = t02 - rv                       # boot / ghost LSB column
    def perturbed2(r, code):
        cur = cur2.copy(); cur[r] = code
        return evolve_to_grid(prev2.copy(), cur, t02, T2, base=ctx2['base'])
    Gg = perturbed2(rv, D1C)
    Gm = perturbed2(rv, LEC)
    cropg = (max(0, rv - 8), rv + 95, max(0, c0 - 75), c0 + 105)
    render_panels(
        [('digit seed in the void beyond the MSB (fixed LSB column, zoomed): a GHOST number running pure x3\n'
          '(no LeastEdge -> no +1, no halving) - x3-bulk dynamics embedded in the real CA - until the host MSB\n'
          '(growing ~log2(3) cols/row) reaches the ghost LSB column and absorbs it by addition; then on-shell again',
          Gg, cropg),
         ('LeastEdge seed at the same cell: BOOTS A SECOND MACHINE (1-cycle engine, front speed 2 cols/row,\n'
          'widening LE wedge). Two fronts = off-shell, but not persistent: the boot column is a permanent LE wall\n'
          'that caps the host MSB; the host is consumed; the tape relaxes to the n=1 shell (verified to T=1400)',
          Gm, band_crop(Gm, max(0, rv - 8), rv + 230))],
        os.path.join(outdir, 'collatz-offshell-void.png'),
        '[real-CA antidiagonal] the void sector: x3 ghosts are absorbed; void-booted machines cap and consume the host')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--sweep', action='store_true')
    ap.add_argument('--longrun', action='store_true')
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--outdir', default=os.path.join(HERE, '..', 'images'))
    a = ap.parse_args()
    if a.verify or a.all:
        if not verify() and not a.sweep and not a.render:
            sys.exit(1)
    if a.sweep or a.all:
        sweep()
    if a.longrun or a.all:
        longrun_voidle()
    if a.render or a.all:
        render_all(os.path.abspath(a.outdir))
