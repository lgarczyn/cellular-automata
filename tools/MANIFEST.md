# tools/ manifest: what each script is actually about

Scope key:
- **[real-CA]** CA.CollatzStep, the actual automaton (3n+1 with LeastEdge halving)
- **[value]** integer Collatz trajectories / statistics (rows of the real CA, so valid, but not spatial)
- **[x3-bulk]** pure multiplication by 3 (ca-mul3.js). Valid about x3; NOT about Collatz
- **[ring]** modular window (mod 2^W or 2^W-1). Wrap artifacts possible; treat with suspicion

## Ground truth
| script | scope | what |
|---|---|---|
| collatz_real.py | [real-CA] | verified port of CA.CollatzStep (rows = odd trajectory) |
| collatz_hex.py | [real-CA] | hex renderer matching the app (MSB left) |
| collatz_bridge.py | [real-CA]+[value] | the bridge: composed tails vs LeastEdge rhythm. Crystal tails = exactly periodic v-seq (2-adic ideal); block boundary located by rhythm to the bit; x3 charge has NO rhythm effect (\|d\| <= 0.1); domain walls radiate a universal ~log2(3) bits/step disorder wedge, charge-blind |
| collatz_offshell.py | [real-CA] | antidiagonal (t=r+c) slice machine, verified cell-exact vs collatz_real; off-shell census: older-slice carries are dead state, flips instantly re-seed another integer's shell (1 broken link), low-bit flips coalesce back, void digit seeds = transient x3 ghosts, void LE seeds boot a parasite machine that caps and consumes the host; no persistent off-shell soliton |
| reproduce_all.py | [real-CA]+[value] | E1..E14 proof-of-work reproduction; NOTE: E5/E14 test finite-seed stopping times, they do not probe bulk-interior structure |
| collatz_compose.py | [real-CA] | THE BLOCK ZOO + SPLICE LAW. Growing blocks = negative 2-adic rational cycles x = c/(2^S-3^l), 2^S < 3^l: word+right-edge motif = the rational's expansion, rhythm = its cycle. 70 blocks (l<=7) all realized as integer tapes and rhythm-locked in the real system. Raw-cut composition = basin of the wall rational (exact, 0/360 exceptions; almost always decay). Designed splice (preimage of A's cycle under B's rhythm) composes ANY over ANY with zero transient; runner law forces the wall digits to be B's own word |
| collatz_render_compose.py | [real-CA] | hex figures for the above: collatz-compose-zoo / -wall / -triple.png, all cell-level CA.CollatzStep runs |
| collatz_leftedge.py | [real-CA] | THE LEFT EDGE. Quantifier (zlib gain / autocorr / const-run, z vs random). LAW 1: above LeastEdge+40 the fresh region = pure x3 flow bit-for-bit (0 mismatches, max ripple 18); LAW 2: real vs synthetic scores agree with margin (the +1s can tip marginal aims at small size). Null field (random, fuse, zoo words, 3-smooth, sparse) = noise. Only structure = ternary aiming n ~ P*2^g/3^k: P crystallizes at step k, then its river. Exhaustive 18-bit scan (0.8% structured, all aims, 25x enrichment); hillclimb plateaus at z~4.6: design-only, no gradient |
| collatz_render_leftedge.py | [real-CA] | hex figures: collatz-leftedge-crystal / -both / -quantifier.png |
| collatz_river.py | [real-CA] | THE FRONT IS A TIME QUASICRYSTAL: MSB-aligned rows agree to -log2\|frac(m*log2 3)\|-1 bits at lag m; peaks at CF convergents 12/41/53/306/359/665 (13 bits at 665); measured = predicted to 0.1 bit, universal, seed-independent. Retracts the flat "river is noise" claim (tape-frame artifact) |
| collatz_bigscan.py | [real-CA] | the big left-edge scan: 2.1M exhaustive 23-bit + 585k random at 48/96/256/700 bits, both frames, 14 cores; every hit mechanism-verified vs the pure x3 flow: all mantissa-explained or affine-tipped, no second per-seed mechanism |
| collatz_render_river.py | [real-CA] | figures: collatz-river-quasicrystal / -leftedge-echoes (a flash echoes at +12/+53/+306/+665, depths as predicted) / -leftedge-layercake.png (independent aims at separate heights) |
| collatz_deepladder.py | [real-CA] | the deep echo ladder: flash at k=40 verified to return at EVERY CF convergent lag of log2(3): 12/53/306/665/15601/31867/79335/111202/190537, depths 6..22 bits = exact predictions (frac computed from integer 3^m, not float) |
| leftscan/ | [real-CA] | C scanners: leftscan.c (4-channel bits-of-evidence: tape rows, front rows, fixed-column time-periodicity, per-seed quasicrystal anomaly; calib at random-max), runall.sh (exhaustive 2^31 32-bit + 2e9 random 64-bit, 16 shards), giantladder.c (libgmp.so direct-ABI runner: 4,573,972-bit tape, 10,590,781 odd steps, echo at lag 10,590,737 = 24 bits vs 22.7 predicted, 977 s) |
| collatz_verifyhits.py | [real-CA] | stage 2 for leftscan: mechanism verification of every hit vs the pure x3 flow + vertical-anomaly re-check |
| collatz_render_ladder.py | [real-CA] | figure: collatz-echo-ladder.png (measured vs predicted echo depth at all 10 convergent rungs) |

## Valid value-map results (statistics of real trajectories)
| script | what |
|---|---|
| collatz_steps.c, plot_collatz.py, collatz.py | stopping times, log-x graph |
| collatz_lattice.py | (a,b) recipe lattice, log2(3) quasicrystal, shear/fold/wrap |
| collatz_reduce.py, collatz_sieve.c | residue reductions, leaves, sieves |
| collatz_dyadic.py, collatz_noise.py | 2-adic self-affine residual, noise cascade |
| collatz_edge.py | MSB edge = t*log2(3)+log2(a/d) instrument |
| collatz_cycles.py, collatz_rational.py | cycle bounds; rational slope iff cycle |
| collatz_halfmachine.py | 2-adic periodic points (cycles), C/(2^a-3^b) |
| collatz_halfrun.py | half machine as fuse: prescribed halving patterns, ~1 bit/step burn, exchange rate log2(3)-1 |
| collatz_runners.py | runner-rhythm lifting + exact fuse law: v-prefix (sum S) = one class mod 2^(S+1); overshoot = 2-adic agreement with rational runner C/(2^S-3^l), geometric tail, 0 exceptions in 640k trials; hex figure of best fuse is [real-CA] |
| collatz_feather.py | trajectory feather art |
| collatz_protocol.py | hailstone-record protocol: climb classes n = (m<<(j+1))-1, pilot sweep, blocker list |
| collatz_monster.py | THE MONSTER HUNT. Designed giants run exactly: 2^(2^20)-1 = 5,044,234 odd steps (peak 1,661,954 bits), 2^(2^22)-1 = 20,229,242 odd steps (peak 6,647,814 bits); both within 1e-7 of the K*log2(3) prediction. Searched champions PROVED class-maximal by exhaustive sweep: 48/16 -> 581, 64/32 -> 710, 80/48 -> 868 odd steps (delay 2324). odd/bit decays 12.10/11.09/10.85 -> 4.81: search bonus dies like ln(size), design scales linearly and without limit |
| collatz_giantshape.py | [real-CA] shape of the giant: whole-life density map in the LeastEdge frame; verifies the climb closed form n_r = 3^r*2^(K-r)-1 (two sectors: 3^r digits left, untouched fuse right, boundary 1 cell/step, MSB edge 1.585) |
| monster/ | C searchers behind the above: monster2.c (random hunt + overflow log), exh.c (exhaustive class sweep, u128 fast path + 512-bit fallback), recheck.c (512-bit exact recheck of discards), longrun.sh / exhrun.sh drivers, giant.py (exact all-ones giant) |

## x3-bulk results (true about x3 only; the "crystals/gliders zoo")
collatz_bulk.py, collatz_build.py, collatz_atlas.py (composition charge law),
collatz_akb.py, collatz_truecomp.py (period-preserving composition census),
collatz_charge3.py (k>=3 weighted charge law: pairwise-forbidden blocks
composing as odd-length words; alternating-sum law at k=4),
collatz_subpatterns.py, collatz_domains.py, collatz_traveling.py (rigid
shifters 3=2^k mod d), collatz_leftmover.py, collatz_leftsearch.py,
collatz_glidersearch.py (x3 digit/carry majority CA, NOT CollatzStep),
collatz_msbscan.py (3^t mantissa), collatz_glider.py.

## Ring windows (artifact-prone)
collatz_loopworlds.py, collatz_ringsize.py, collatz_branchplace.py. The
"block-of-ones fixed point" was an end-around-carry artifact; retracted in
COLLATZ.md.

## Retracted / superseded claims (see COLLATZ.md postscripts)
- block-of-ones as zero-halving fixed point (mod artifact)
- "unit cells must be uniform textures" (false; AAB etc exist)
- "no localized left-mover, provably" (proved only for x3-bulk linearity)
- "crystals are not special" (true only for finite-seed stopping times)
