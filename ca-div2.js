"use strict";

CA.DivBy2 = class DivBy2 extends CA.CellularAutomaton {

  constructor() {
    super({
      name:        'Division by 2',
      description: 'Each cell copies its upper-left neighbor — a 1-input rule that produces a bit-shift. '
                 + 'Integer division by 2, from the simplest possible CA.',
      blankState:  0,
      seedRows:    1,
      displayMode: 'grid',
    });
  }

  suggestSize(input) {
    const b = CA.CellularAutomaton.bitLength(input);
    return { width: b + 1, height: b + 1 };
  }

  initGrid(input) {
    const n    = typeof input === 'number' ? input : parseInt(input) || 0;
    const bits = CA.CellularAutomaton.toBitsMSB(n, this.width);
    for (let c = 0; c < this.width; c++) this.grid[0][c] = bits[c];
  }

  computeCell(r, c) { return this.get(r-1, c-1); }

  sourceCells(r, c) {
    if (r === 0) return [];
    return [{r: r-1, c: c-1}];
  }

  cellStyle(v) {
    return v === 1
      ? { text: '1', colors: ['#3fb950'], fg: '#000' }
      : { text: '0', colors: ['#1a1e24'], fg: '#444' };
  }

  readRow(r) {
    let n = 0;
    for (let c = 0; c < this.width; c++) n = n * 2 + this.get(r, c);
    return n;
  }
};
