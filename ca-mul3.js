"use strict";

// Multiply by 3: each row = 3 * (row above).
// 3x = 2x + x.  The 2x is a left bit-shift, so for column c:
//   shifted = digit(r-1, c-1)   ← the "2x" bit
//   same    = digit(r-1, c)     ← the "1x" bit
//   carry   = carry(r, c-1)     ← carry from the cell to the left (same row)
//   sum     = shifted + same + carry
//   digit   = sum mod 2
//   carry   = 1 if sum >= 2
//
// Cells are { digit, carry } objects. Null = blank.

CA.MulBy3 = class MulBy3 extends CA.CellularAutomaton {

  constructor({ displayMode = 'grid' } = {}) {
    super({
      name:         displayMode !== 'grid' ? 'Multiply by 3 (Hex)' : 'Multiply by 3',
      description:  'Each row is 3× the row above, computed as 2x + x. '
                  + 'The 2x term is a bit-shift: the digit at (r−1, c−1). '
                  + 'The 1x term is the digit directly above: (r−1, c). '
                  + 'These two are summed with the carry from the left neighbour (r, c−1). '
                  + 'If the sum is 2 or 3, a carry (orange outline) propagates rightward.',
      blankState:   null,
      seedRows:     1,
      displayMode,
      hexGroupSize: 4,
    });
  }

  suggestSize(input) {
    const b = CA.CellularAutomaton.bitLength(input);
    const h = b + 4;
    return { width: b + 2 * h + 2, height: h };
  }

  initGrid(input) {
    const n    = typeof input === 'number' ? input : parseInt(input) || 0;
    const bits = CA.CellularAutomaton.toBitsLSB(n, this.width);
    const msb  = Math.max(1, CA.CellularAutomaton.bitLength(n));
    for (let c = 0; c < this.width; c++)
      this.grid[0][c] = c < msb ? { digit: bits[c] ?? 0, carry: 0 } : null;
  }

  computeCell(r, c) {
    const shifted  = this.get(r - 1, c - 1);   // 2x bit (left-shifted)
    const same     = this.get(r - 1, c);        // 1x bit
    const left     = this.get(r, c - 1);        // same-row left neighbour
    const carryIn  = left?.carry ?? 0;
    if (shifted === null && same === null && carryIn === 0) return null;
    const sum = (shifted?.digit ?? 0) + (same?.digit ?? 0) + carryIn;
    return { digit: sum % 2, carry: sum >= 2 ? 1 : 0 };
  }

  sourceCells(r, c) {
    if (r === 0) return [];
    const s = [];
    s.push({r: r-1, c: c-1}); // shifted (2x)
    s.push({r: r-1, c: c});   // same (1x)
    if (c > 0) s.push({r: r, c: c-1}); // carry from left
    return s;
  }

  cellStyle(cell) {
    if (cell === null) return { text: '', colors: ['#0d1117'], fg: '#222', carry: false };
    return {
      text:   String(cell.digit),
      colors: [cell.digit ? '#7c3aed' : '#1a1e24'],
      fg:     cell.digit ? '#fff' : '#444',
      carry:  cell.carry > 0,
    };
  }

  readRow(r) {
    let n = 0;
    for (let c = this.width - 1; c >= 0; c--) {
      const cell = this.get(r, c);
      if (cell !== null) n = n * 2 + cell.digit;
    }
    return n;
  }
};
