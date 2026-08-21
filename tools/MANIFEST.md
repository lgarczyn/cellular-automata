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
| reproduce_all.py | [real-CA]+[value] | E1..E14 proof-of-work reproduction; NOTE: E5/E14 test finite-seed stopping times, they do not probe bulk-interior structure |

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
| collatz_feather.py | trajectory feather art |

## x3-bulk results (true about x3 only; the "crystals/gliders zoo")
collatz_bulk.py, collatz_build.py, collatz_atlas.py (composition charge law),
collatz_akb.py, collatz_truecomp.py (period-preserving composition census),
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
