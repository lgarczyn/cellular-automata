# CLAUDE.md: read before touching the Collatz research

This repo is a CA visualizer plus a long-running research program (COLLATZ.md).
A previous run of this program lost weeks of signal to vocabulary mismatches.
The rules below exist because each one was violated and caught.

## What "the automaton" means

**CA.CollatzStep** (ca-collatz-step.js), rendered as hexagons (CollatzHex).
Ground-truth Python port: `tools/collatz_real.py`. It is VERIFIED: each display
row is one odd Collatz step (3n+1 then strip trailing zeros); seed 27 gives
rows 27, 41, 31, 47, 71, 107, 161, ... Any new simulator must reproduce this
before its output is trusted.

- Display rows are NOT the machine state. The causal time slices are the
  antidiagonals t = r + c. The carry crosses those slices, so the interior
  state is 2 bits per cell: (digit, carry). The 6 display tiles are
  0, 0+, 1, 1+, null (beyond-MSB), LeastEdge (right edge).
- "Diagonalized CA" in Lou's words = this antidiagonal frame.
- Do NOT substitute: pure x3 (ca-mul3.js) is a different automaton ("the
  bulk"); integer trajectory statistics are "the value map"; mod 2^W or
  mod 2^W-1 rings are lossy windows whose wrap creates artifacts (a fake
  block-of-ones fixed point came from end-around carry). Results must be
  labeled with their model: [real-CA], [x3-bulk], [value], [ring].

## Vocabulary (Lou's usage)

- "left" = toward MSB. Drawn on the LEFT, always. Growth side, rate log2(3).
- "right" = LSB side. The LeastEdge ("the right side eats") consumes there.
- "runners" = the activity rhythm at the right/LeastEdge interface (halvings).
- "loop the X side" = periodic boundary as a window into a much larger CA
  ("we are in the middle of a giant number"). A lens, not modular arithmetic.
  Any conclusion that depends on the wrap is invalid.
- "pattern" = a spatial tile texture in the hex view. Answers about patterns
  are hex tile pictures, not integers or fractions.
- "half machine" = periodic/looping right side + free growing left edge. One
  edge loops, one does not. A full cycle (both edges looping) is NOT it.
- "composition" = combined patterns that keep their parts' identity (period,
  visible sections). "The orbit eventually closes" is persistence, not
  composition.

## Method rules

1. When asked to make / find / try X: run a real search in the exact system
   and show hex pictures of the best attempts. Never answer with an
   impossibility proof in a different model. Proofs come after, scoped.
2. If a result refutes Lou's idea, suspect the model or the translation
   first. He caught 6+ real modeling errors in one session.
3. Rendering: MSB left; hex tiles or square cells (aspect 1); show whole
   clean loops cropped to the minimal repeating unit; no seed transients;
   state the model scope in the figure title.
4. `tools/MANIFEST.md` classifies every script by model and status. Check it
   before reusing or citing a result.
5. COLLATZ.md is a lab notebook including errors and retractions; its top
   section states what currently stands.
