// Complex arithmetic + Riemann zeta / completed xi evaluation.
// Works in the browser (globals) and in node (module.exports) for testing.

const ZM = (() => {
  'use strict';

  // ---- complex helpers: {re, im} ----
  const C = (re, im = 0) => ({ re, im });
  const add = (a, b) => C(a.re + b.re, a.im + b.im);
  const sub = (a, b) => C(a.re - b.re, a.im - b.im);
  const mul = (a, b) => C(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
  const div = (a, b) => {
    const d = b.re * b.re + b.im * b.im;
    return C((a.re * b.re + a.im * b.im) / d, (a.im * b.re - a.re * b.im) / d);
  };
  const conj = (a) => C(a.re, -a.im);
  const abs = (a) => Math.hypot(a.re, a.im);
  const arg = (a) => Math.atan2(a.im, a.re);
  const cexp = (a) => {
    const r = Math.exp(a.re);
    return C(r * Math.cos(a.im), r * Math.sin(a.im));
  };
  const clog = (a) => C(Math.log(abs(a)), arg(a));
  // real base b > 0 raised to complex exponent
  const rpow = (b, s) => cexp(mul(C(Math.log(b), 0), s));
  const cpow = (a, s) => cexp(mul(clog(a), s));
  const csin = (a) => C(Math.sin(a.re) * Math.cosh(a.im), Math.cos(a.re) * Math.sinh(a.im));

  const ONE = C(1);
  const PI = Math.PI;

  // ---- complex gamma: Lanczos approximation (g = 7, 9 terms) ----
  const LG = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
  ];
  function gamma(z) {
    if (z.re < 0.5) {
      // reflection: Γ(z) = π / (sin(πz) Γ(1−z))
      return div(C(PI), mul(csin(mul(C(PI), z)), gamma(sub(ONE, z))));
    }
    z = sub(z, ONE);
    let x = C(LG[0]);
    for (let i = 1; i < LG.length; i++) x = add(x, div(C(LG[i]), add(z, C(i))));
    const t = add(z, C(7.5));
    // Γ(z+1) = √(2π) · t^(z+0.5) · e^(−t) · x
    return mul(mul(C(Math.sqrt(2 * PI)), mul(cpow(t, add(z, C(0.5))), cexp(C(-t.re, -t.im)))), x);
  }

  // ---- eta via Borwein's algorithm ----
  const N = 50;
  const D = (() => {
    // d_k = n · Σ_{i=0..k} (n+i−1)! 4^i / ((n−i)! (2i)!)
    const d = new Array(N + 1);
    let term = 1; // i = 0 term of the inner sum, times n: n·(n−1)!/n! = 1
    let sum = 1;
    d[0] = 1;
    for (let i = 1; i <= N; i++) {
      term *= (4 * (N + i - 1) * (N - i + 1)) / (2 * i * (2 * i - 1));
      sum += term;
      d[i] = sum;
    }
    return d;
  })();
  const LOGK = Array.from({ length: N }, (_, k) => Math.log(k + 1));
  const LN2 = Math.LN2;

  // ζ(s) for Re(s) ≥ 0.5 : ζ = η(s) / (1 − 2^(1−s))
  function zetaRight(s) {
    let sr = 0, si = 0;
    for (let k = 0; k < N; k++) {
      // (−1)^k (d_k − d_N) (k+1)^(−s)
      const m = Math.exp(-s.re * LOGK[k]) * (D[k] - D[N]) * (k & 1 ? -1 : 1);
      const ang = -s.im * LOGK[k];
      sr += m * Math.cos(ang);
      si += m * Math.sin(ang);
    }
    const eta = C(-sr / D[N], -si / D[N]);
    const denom = sub(ONE, rpow(2, sub(ONE, s)));
    return div(eta, denom);
  }

  // χ(s) = 2^s π^(s−1) sin(πs/2) Γ(1−s)  — the "fold factor"
  function chi(s) {
    return mul(
      mul(rpow(2, s), rpow(PI, sub(s, ONE))),
      mul(csin(mul(C(PI / 2), s)), gamma(sub(ONE, s)))
    );
  }

  // ζ(s) anywhere: functional equation ζ(s) = χ(s) ζ(1−s) for the left half
  function zeta(s) {
    if (Math.hypot(s.re, s.im) < 1e-8) return C(-0.5); // χ(0)·ζ(1) is 0·∞
    return s.re >= 0.5 ? zetaRight(s) : mul(chi(s), zetaRight(sub(ONE, s)));
  }

  // ξ(s) = ½ s(s−1) π^(−s/2) Γ(s/2) ζ(s)  — the unfolded, mirror-symmetric completion
  function xi(s) {
    // removable 0·∞ at s = 0 and s = 1 (the pole of Γ(s/2) resp. ζ(s) cancels)
    if (Math.hypot(s.re, s.im) < 1e-8 || Math.hypot(s.re - 1, s.im) < 1e-8) return C(0.5);
    const pre = mul(C(0.5), mul(s, sub(s, ONE)));
    return mul(mul(pre, mul(rpow(PI, C(-s.re / 2, -s.im / 2)), gamma(C(s.re / 2, s.im / 2)))), zeta(s));
  }

  return { C, add, sub, mul, div, conj, abs, arg, cexp, clog, rpow, cpow, csin, gamma, chi, zeta, xi };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = ZM;
