"use strict";

// Collatz procedure encoded as a CA.
// Cells are { digit, carry } objects. Null = blank.
// Rule: sum = digit(r-1,c+1) + digit(r-2,c+1) + carry(r-1,c)
//       new digit = sum mod 2,  new carry = floor(sum / 2)
// A null propagates rightward; a cell goes null when its left neighbor
// is null and its right neighbor has an even digit.

CA.Collatz = class Collatz extends CA.CellularAutomaton {

  constructor({ displayMode = 'grid' } = {}) {
    super({
      name:         displayMode !== 'grid' ? 'Collatz (Hex)' : 'Collatz (Binary)',
      description:  'The Collatz procedure from 6 tile types and local matching rules.',
      blankState:   null,
      seedRows:     2,
      displayMode,
      hexGroupSize: 4,
    });
  }

  suggestSize(input) {
    const b = CA.CellularAutomaton.bitLength(input);
    return { width: b + 30, height: 120 };
  }

  initGrid(input) {
    const n    = typeof input === 'number' ? input : parseInt(input) || 1;
    const bits = CA.CellularAutomaton.toBitsLSB(n, this.width);
    const msb  = CA.CellularAutomaton.bitLength(n);

    // Row 0: binary digits LSB-first, null beyond MSB
    for (let c = 0; c < this.width; c++)
      this.grid[0][c] = c < msb ? { digit: bits[c] ?? 0, carry: 0 } : null;

    // Row 1: computed from row 0, treating row -1 as all-null
    for (let c = 0; c < this.width; c++)
      this.grid[1][c] = this._cell(this.get(0, c+1), this.get(0, c), null);
  }

  computeCell(r, c) {
    return this._cell(this.get(r-1, c+1), this.get(r-1, c), this.get(r-2, c+1));
  }

  _cell(rp, sp, rp2) {
    if (rp === null) return null;
    if (sp === null && rp.digit === 0) return null;
    const sum = (rp?.digit ?? 0) + (rp2?.digit ?? 0) + (sp?.carry ?? 0);
    return { digit: sum % 2, carry: Math.floor(sum / 2) };
  }

  sourceCells(r, c) {
    if (r <= 1) return []; // seed rows
    const s = [];
    s.push({r: r-1, c: c+1}); // rp
    s.push({r: r-1, c: c});   // sp (carry)
    s.push({r: r-2, c: c+1}); // rp2
    return s;
  }

  cellStyle(cell) {
    if (cell === null) return { text: '', colors: ['#0d1117'], fg: '#222', carry: false };
    const c = cell.carry > 0;
    return {
      text:   String(cell.digit),
      colors: [cell.digit ? (c ? '#3fb950' : '#2ea043') : (c ? '#1e2a1e' : '#1a1e24')],
      fg:     cell.digit ? '#fff' : (c ? '#666' : '#555'),
    };
  }

  readRow(r) {
    if (r < 0 || r >= this.height) return null;
    let n = 0;
    for (let c = this.width - 1; c >= 0; c--) {
      const cell = this.get(r, c);
      if (cell !== null) n = n * 2 + cell.digit;
    }
    return n;
  }
};
