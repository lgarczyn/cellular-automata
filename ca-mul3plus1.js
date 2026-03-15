"use strict";

// 3x + 1: identical to Multiply by 3, but with carry-in = 1 at column 0.
// Column 0 is a LeastEdge cell — always digit=0, carry=1.
// Any cell with a LeastEdge above it also becomes a LeastEdge.

CA.MulBy3Plus1 = class MulBy3Plus1 extends CA.MulBy3 {

  constructor({ displayMode = 'grid' } = {}) {
    super({ displayMode });
    this.name = '3x + 1';
    this.description =
      'Each row is 3×(row above) + 1. Same as ×3, but the LSB carry is forced to 1, '
    + 'which adds 1 at every step. The rightmost column shows the injected +1 carry.';
  }

  suggestSize(input) {
    const size = super.suggestSize(input);
    return { width: size.width + 1, height: size.height };
  }

  initGrid(input) {
    const n    = typeof input === 'number' ? input : parseInt(input) || 0;
    const bits = CA.CellularAutomaton.toBitsLSB(n, this.width);
    const msb  = Math.max(1, CA.CellularAutomaton.bitLength(n));
    this.grid[0][0] = CA.LEAST_EDGE;
    for (let c = 1; c < this.width; c++)
      this.grid[0][c] = c - 1 < msb ? { digit: bits[c - 1] ?? 0, carry: 0 } : null;
  }

  computeCell(r, c) {
    const above = this.get(r - 1, c);
    if (above === CA.LEAST_EDGE) return CA.LEAST_EDGE;

    const shifted = this.get(r - 1, c - 1);
    const same    = above;
    const left    = this.get(r, c - 1);
    const carryIn = left?.carry ?? 0;
    if (shifted === null && same === null && carryIn === 0) return null;
    const sum = (shifted?.digit ?? 0) + (same?.digit ?? 0) + carryIn;
    return { digit: sum % 2, carry: sum >= 2 ? 1 : 0 };
  }

  cellStyle(cell) {
    if (cell === CA.LEAST_EDGE) return {
      text: '0', colors: ['#1b2a1b'], fg: '#3fb950', carry: true,
    };
    return super.cellStyle(cell);
  }

  readRow(r) {
    let n = 0;
    for (let c = this.width - 1; c >= 0; c--) {
      const cell = this.get(r, c);
      if (cell !== null && cell !== CA.LEAST_EDGE) n = n * 2 + cell.digit;
    }
    return n;
  }
};
