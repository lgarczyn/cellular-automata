# The certified absolute monster: all-ones seed of 2^20 bits, exact full run.
import time, json
K = 1 << 20
n = (1 << K) - 1
t0 = time.time()
s = 0
peak_bits = K
CHK = 200000
while n != 1:
    m = 3 * n + 1
    v = (m & -m).bit_length() - 1
    n = m >> v
    s += 1
    b = n.bit_length()
    if b > peak_bits:
        peak_bits = b
    if s % CHK == 0:
        with open("giant_progress.json", "w") as f:
            json.dump({"steps": s, "bits": b, "peak": peak_bits,
                       "elapsed": time.time() - t0}, f)
with open("giant_done.json", "w") as f:
    json.dump({"seed_bits": K, "odd_steps": s, "peak_bits": peak_bits,
               "elapsed": time.time() - t0}, f)
print("DONE", s, peak_bits)
