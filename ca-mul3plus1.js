"use strict";

// 3x + 1: identical to Multiply by 3, but with carry-in = 1 at column 0.
// Column 0 is a LeastEdge cell — always digit=0, carry=1.
// Any cell with a LeastEdge above it also becomes a LeastEdge.

CA.MulBy3Plus1 = class MulBy3Plus1 extends CA.MulBy3 {

  constructor({ displayMode = 'grid' } = {}) {
    super({ displayMode });
    this.name = '3x + 1';
    this.description =
      'Same rule as ×3, but the boundary tile (LeastEdge) injects a permanent carry of 1. '
    + 'One tile change turns multiplication into 3x+1.';
  }

  suggestSize(input, height) {
    const size = super.suggestSize(input, height);
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

  cellStyle(cell, r, c) {
    if (cell === CA.LEAST_EDGE) {
      // Only show LeastEdge style for the leftmost one (boundary)
      const right = (r !== undefined && c !== undefined) ? this.get(r, c + 1) : null;
      if (right === CA.LEAST_EDGE) {
        return { text: '', colors: ['#0d1117'], fg: '#333', hidden: true };
      }
      return { text: '0+', colors: ['#1b2a1b'], fg: '#3fb950' };
    }
    return super.cellStyle(cell, r, c);
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
