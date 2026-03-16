"use strict";

// Collatz step: 3x+1 with automatic /2.
// Same as 3x+1, but LeastEdge also spreads diagonally:
// if a cell computes to digit 0 and the cell above-right is LeastEdge,
// it becomes LeastEdge — effectively dividing by 2.

CA.CollatzStep = class CollatzStep extends CA.MulBy3Plus1 {

  constructor({ displayMode = 'grid' } = {}) {
    super({ displayMode });
    this.name = '3x+1 / 2';
    this.description =
      'Collatz step: 3x+1 then divide out factors of 2. '
    + 'The LeastEdge expands diagonally into trailing zeros, performing /2 automatically.';
  }

  analyzeSequence(input) {
    let n = BigInt(input);
    let steps = 0;
    let totalHalvings = 0;
    let maxWidth = 0;
    while (n > 1n) {
      if (n % 2n === 0n) {
        n = n / 2n;
        totalHalvings++;
      } else {
        n = 3n * n + 1n;
        steps++;
      }
      const needed = totalHalvings + CA.CellularAutomaton.bitLength(Number(n));
      if (needed > maxWidth) maxWidth = needed;
    }
    return { steps, maxWidth };
  }

  suggestSize(input) {
    const { steps, maxWidth } = this.analyzeSequence(input);
    return { width: maxWidth + 10, height: steps + 2 };
  }

  run(input, width, height) {
    const size = this.suggestSize(input);
    this.allocate(width ?? size.width, height ?? size.height);
    this.initGrid(input);
    let lastRow = 0;
    for (let r = this.seedRows; r < this.height; r++) {
      this.computeRow(r);
      lastRow = r;
      const val = this.readRow(r);
      if (val === 1 || val === 0) break;
    }
    // Trim unused rows
    this.grid.length = lastRow + 1;
    this.height = this.grid.length;
    return this.grid;
  }

  readRow(r) {
    // Find the first non-LeastEdge column (the LSB of the actual number)
    let start = 0;
    while (start < this.width && this.get(r, start) === CA.LEAST_EDGE) start++;
    let n = 0;
    for (let c = this.width - 1; c >= start; c--) {
      const cell = this.get(r, c);
      if (cell !== null && cell !== CA.LEAST_EDGE) n = n * 2 + cell.digit;
    }
    return n;
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
    const digit = sum % 2;
    const carry = sum >= 2 ? 1 : 0;

    // if (above?.digit == 0 && left === CA.LEAST_EDGE) return CA.LEAST_EDGE;
    if (left === CA.LEAST_EDGE)
    {
      if (digit === 0 && carry == 1) return CA.LEAST_EDGE;
      // special case when starting with even inputs
      if (above?.digit === 0 && shifted === CA.LEAST_EDGE) return CA.LEAST_EDGE;
    }


    return { digit, carry };
  }
};
