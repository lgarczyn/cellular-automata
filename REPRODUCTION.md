# Reproduction on the real automaton (CA.CollatzStep)

Proof-of-work log. Images in images/repro/.

```

## E1 Trajectory + stopping time (the core int operation: 3n+1 then /2)
   seed 27  : real-CA rows == odd trajectory: True ; 41 odd-steps to 1
      rows[:8] = [27, 41, 31, 47, 71, 107, 161, 121]
   seed 703 : real-CA rows == odd trajectory: True ; 62 odd-steps to 1
      rows[:8] = [703, 1055, 1583, 2375, 3563, 5345, 4009, 3007]
   seed 871 : real-CA rows == odd trajectory: True ; 65 odd-steps to 1
      rows[:8] = [871, 1307, 1961, 1471, 2207, 3311, 4967, 7451]

## E2 (a,b) recipe decomposition: a halvings, b triplings, s=a+b
   n=27  : b(triplings)=41  a(halvings)=70  total steps s=111 ; check 2^a ~ n*3^b: 2^70=1.181e+21 vs n*3^41=9.848e+20
   n=97  : b(triplings)=43  a(halvings)=75  total steps s=118 ; check 2^a ~ n*3^b: 2^75=3.778e+22 vs n*3^43=3.184e+22
   n=703 : b(triplings)=62  a(halvings)=108 total steps s=170 ; check 2^a ~ n*3^b: 2^108=3.245e+32 vs n*3^62=2.682e+32

## E3 stopping-time records (the log-x graph is these, one dot each)
   record holders < 2e5 (n, odd-steps): [(26623, 113), (34239, 114), (35655, 119), (52527, 125), (77031, 129), (106239, 130), (142587, 138), (156159, 141)]

## E4 density of 1s -> slow descent (all-ones climbs)
   all-ones 2^40-1  density 1.00 -> 191 odd steps, avg v=1.796
   random 40-bit    density 0.70 -> 119 odd steps, avg v=1.916
   sparse           density 0.07 -> 56 odd steps, avg v=2.304

## E5 x3-crystals are NOT special on the real automaton
   crystal d=7  : 107 steps vs random-same-density 5th-95th 63-192 (inside band)
   crystal d=13 :  35 steps vs random-same-density 5th-95th 64-172 (inside band)
   crystal d=11 :  33 steps vs random-same-density 5th-95th 63-191 (inside band)

## E6 edge balance: growth log2(3) vs consumption v (survival condition)
   all-ones 2^50-1  v=1.824 halvings/step, net -0.239 bits/step (log2 3 - v) -> shrinks
   random 50-bit    v=1.984 halvings/step, net -0.399 bits/step (log2 3 - v) -> shrinks

## E7 the only cycle is 1 (no crystals/gliders can be periodic)
   odd seeds < 1e5 that fail to reach 1 in 1e5 steps: 0 (all reach 1)

## E8 the carry texture is Rule-60-with-carries (melted Sierpinski) - visible in hex

## E9 the (a,b) lattice / log2(3) quasicrystal (value-based, real Collatz)
   b (triplings) grows 2.1714 per doubling of n (theory 1/log2(4/3)=2.4094)

## E10 left/MSB edge = t*log2(3)+log2(n0) instrument (value-based)
   n=77031: trajectory length 130; leading-bit growth follows x3 (log2 3) per odd step
   n=703: trajectory length 63; leading-bit growth follows x3 (log2 3) per odd step

## E11 half-open (looping right tail): a periodic-tail seed under the real CA
   periodic-tail seed (41 bits) descends in 126 odd steps (no special persistence)

## E12 loop-MSB / slow-LSB: which patterns halve least (slowest descent)
   2^16-1 (all ones): avg v=1.955 (the minimum; slowest LSB eating)
   2^24-1 (all ones): avg v=1.724 (the minimum; slowest LSB eating)
   2^32-1 (all ones): avg v=1.784 (the minimum; slowest LSB eating)

## E13 dump a repeating pattern block, real CA (hex)
   crystal-block seed (85 bits) -> 292 odd steps; pattern shows as diagonal stripes then descends

## E14 x3 'traveling crystals' do NOT travel in the real CA
   d=13 crystal seed: under x3 it shifts left 4/step; under real CA -> descends in 81 steps (no translation)
```
