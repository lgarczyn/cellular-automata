"use strict";

// A TRUE cellular automaton for the shortcut Collatz map
//   T(n) = n/2        if n even
//   T(n) = (3n+1)/2   if n odd
//
// Every other arithmetic automaton on this page is a "quasi-CA"
// (Cloney, Goles & Vichniac, 1987): computeCell peeks at this.get(r, c-1)
// in the CURRENT row, so carries ripple sequentially inside a row and the
// cells are not really updated simultaneously. This one reads only row r-1.
// Cells can be computed in any order — see the reverse-order test in test.js.
//
// Two ideas make it possible:
//
// 1. Base 6. Because 6 = 2·3:
//      - halving is digit-local:  floor(n/2)_i = floor(d_i/2) + 3·(d_{i+1} mod 2)
//      - tripling never cascades: (3n)_i = 3·(d_i mod 2) + floor(d_{i-1}/2) ≤ 5,
//        so a carry dies after one cell.
//    And for odd n, (3n+1)/2 = 3·floor(n/2) + 2, so BOTH branches start by
//    halving: with h = floor(n/2),
//      T(n) = h                              (n even)
//      T(n)_i = 3·(h_i mod 2) + floor(h_{i-1}/2) + 2·[i=0]   (n odd)
//
// 2. Skewed time. The odd/even decision lives in digit 0, and no local rule
//    can broadcast it to every digit in a single row. So one Collatz step is
//    NOT one row: digit i of iterate k is computed at row 2k + i - 1, and
//    each iterate appears along a diagonal, a new one launched every 2 rows.
//    The parity bit p and the halved digit h hop along with the update wave,
//    one column per row — which is exactly as fast as causality allows.
//
// Cell state: { d, h, p, fresh }
//   d     — current base-6 digit
//   h     — halved digit computed at this cell's last update (read by the
//           right neighbor one row later)
//   p     — parity of the iterate being consumed (relayed from digit 0)
//   fresh — true on the row this cell just recomputed d; the left neighbor's
//           fresh flag is what tells a cell "your turn next row".

CA.CollatzBase6 = class CollatzBase6 extends CA.CellularAutomaton {

  constructor() {
    super({
      name:        '3x+1 / 2 in Base 6 — a true CA',
      description:
        'The automata above cheat: carries ripple sideways inside a row, so cells '
      + 'are not updated simultaneously. In base 6 (= 2·3) the shortcut Collatz map '
      + 'needs no carry chains — halving looks one digit up, tripling one digit down, '
      + 'and carries die after one cell. Every cell here is computed from just the '
      + 'three cells above it, all at once. The price: parity news from the last digit '
      + 'travels one column per row, so one Collatz step is not one row — each iterate '
      + 'is a bright diagonal, with a new step launched every two rows.',
      blankState:  null,
      seedRows:    1,
      displayMode: 'grid',
    });
  }

  analyzeSequence(input) {
    const digitCount = (v) => {
      let len = 0;
      for (let m = v; m > 0n; m /= 6n) len++;
      return Math.max(1, len);
    };
    let n = BigInt(input);
    if (n < 1n) n = 1n;
    let steps = 0;
    let maxLen = digitCount(n);
    let height = 1;
    while (n > 1n && steps < 20000) {
      n = n % 2n === 1n ? (3n * n + 1n) / 2n : n / 2n;
      steps++;
      const len = digitCount(n);
      if (len > maxLen) maxLen = len;
      // digit i of iterate k lands at row 2k + i - 1
      const needed = 2 * steps + len - 1;
      if (needed > height) height = needed;
    }
    return { steps, maxLen, height };
  }

  suggestSize(input) {
    const { maxLen, height } = this.analyzeSequence(input);
    return { width: maxLen + 1, height };
  }

  initGrid(input) {
    let n = BigInt(typeof input === 'number' ? input : parseInt(input) || 1);
    if (n < 1n) n = 1n;
    let c = 0;
    while (n > 0n && c < this.width) {
      this.grid[0][c++] = { d: Number(n % 6n), h: 0, p: 0, fresh: false };
      n /= 6n;
    }
  }

  computeCell(r, c) {
    const me    = this.get(r - 1, c);
    const left  = this.get(r - 1, c - 1);
    const right = this.get(r - 1, c + 1);

    if (me === null) {
      // Frontier blank: when the update wave reaches the neighbor below us
      // in significance, check whether the number grew a digit. Our own
      // digit and everything above are 0, so h here is 0 and the new digit
      // is just the incoming carry floor(h_left / 2) — and only on odd steps.
      if (left === null || !left.fresh) return null;
      if (left.p !== 1) return null;
      const d = Math.floor(left.h / 2);
      if (d === 0) return null;
      return { d, h: 0, p: left.p, fresh: true };
    }

    // Digit 0 is the only active cell with a blank left neighbor (digits are
    // contiguous and never deactivate), so it self-clocks every other row;
    // everyone else fires the row after their left neighbor did.
    const isLSB = left === null;
    const update = isLSB ? !me.fresh : left.fresh;
    if (!update) return { d: me.d, h: me.h, p: me.p, fresh: false };

    const h = Math.floor(me.d / 2) + 3 * ((right === null ? 0 : right.d) % 2);
    const p = isLSB ? me.d % 2 : left.p;
    const d = p === 1
      ? 3 * (h % 2) + Math.floor((isLSB ? 0 : left.h) / 2) + (isLSB ? 2 : 0)
      : h;
    return { d, h, p, fresh: true };
  }

  sourceCells(r, c) {
    if (r === 0) return [];
    const me = this.get(r, c);
    if (me === null) return [];
    if (!me.fresh) return [{ r: r - 1, c }];
    return [{ r: r - 1, c: c + 1 }, { r: r - 1, c }, { r: r - 1, c: c - 1 }];
  }

  // Iterate k lives on a diagonal: digit i at row 2k + i - 1 (seed row for k=0).
  readIterate(k) {
    let n = 0n;
    for (let i = this.width - 1; i >= 0; i--) {
      const r = k === 0 ? 0 : 2 * k + i - 1;
      const cell = r >= 0 && r < this.height ? this.get(r, i) : null;
      n = n * 6n + BigInt(cell === null ? 0 : cell.d);
    }
    return n;
  }

  // Odd rows are where digit 0 of a new iterate appears; label them with
  // the value of the iterate whose diagonal starts there.
  readRow(r) {
    if (r === 0) return this.readIterate(0).toString();
    if (r % 2 === 1) return this.readIterate((r + 1) / 2).toString();
    return null;
  }

  // Row-0 cells are base-6 digits, not bits — the binary click-toggle
  // doesn't apply.
  bitColToIndex(c) { return -1; }

  cellStyle(cell, r, c) {
    const FRESH = ['#21262d', '#9e6a03', '#1f6feb', '#bc4c00', '#238636', '#da3633'];
    const HELD  = ['#161b22', '#3a2905', '#102e63', '#451e04', '#0e3517', '#4f1519'];
    if (cell.fresh) {
      return { text: String(cell.d), colors: [FRESH[cell.d]], fg: cell.d === 0 ? '#666' : '#fff' };
    }
    return { text: String(cell.d), colors: [HELD[cell.d]], fg: '#4d5761' };
  }
};
