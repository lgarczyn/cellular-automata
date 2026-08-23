#!/usr/bin/env python3
"""The echo ladder figure. SCOPE: [real-CA].
Measured echo depths of a designed flash (P=1 at k=40) at every
continued-fraction convergent lag of log2(3), from real runs:
the largest is a 4.58M-bit tape run for 10,630,781 odd steps.
Data pasted from tools/collatz_deepladder.py and the GMP runner
(tools/leftscan/giantladder.c); predictions are exact.
"""
import os
import sys
from math import log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collatz_deepladder import predicted_depth

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")

# lag -> measured echo depth (bits), real runs
MEASURED = {
    12: 6, 53: 8, 306: 8, 665: 14, 15601: 14, 31867: 17,
    79335: 17, 111202: 18, 190537: 22,
}
GIANT = None      # filled below from the runner output if present


def main():
    meas = dict(MEASURED)
    gpath = "/var/tmp/collatz-scratch/leftscan/giant_out.txt"
    if os.path.exists(gpath):
        for line in open(gpath):
            if line.startswith("echo at k+"):
                parts = line.split()
                lag = int(parts[2].replace("k+", "")) if False else \
                    int(line.split("k+")[1].split()[0])
                depth = int(line.split("depth")[1].split()[0])
                meas[lag] = depth
    lags = sorted(meas)
    pred = [predicted_depth(m) for m in lags]
    vals = [meas[m] for m in lags]
    fig, ax = plt.subplots(figsize=(11.5, 6), dpi=140)
    ax.plot(lags, pred, "--o", color="#39d353", ms=5,
            label="predicted: -log2|frac(m*log2 3)| - 1 (exact arithmetic)")
    ax.plot(lags, vals, "o-", color="#7c3aed", ms=6, lw=1.4,
            label="measured echo depth (real runs)")
    for m, v in meas.items():
        ax.annotate(str(m), (m, v), textcoords="offset points",
                    xytext=(0, 9), fontsize=8, color="#4c2f9e", ha="center")
    ax.set_xscale("log")
    ax.set_xlabel("echo lag m = continued-fraction convergent denominator "
                  "of log2(3)")
    ax.set_ylabel("depth of the returning flash (leading bits)")
    ax.grid(alpha=0.25, which="both")
    ax.legend(loc="upper left", fontsize=9.5)
    big = max(meas)
    ax.set_title("[real-CA] the echo ladder: a flash designed at step 40 "
                 "returns at every convergent lag of log2(3).\nLargest rung: "
                 "lag %s on a %s tape - the pattern is still readable %s "
                 "steps after it was scheduled, %d bits deep."
                 % ("{:,}".format(big),
                    "4,573,972-bit" if big > 1e6 else "82,286-bit",
                    "{:,}".format(big), meas[big]), fontsize=11)
    out = os.path.join(IMG, "collatz-echo-ladder.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out, "| points:", meas)


if __name__ == "__main__":
    main()
