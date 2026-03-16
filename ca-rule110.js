"use strict";

CA.Rule110 = class Rule110 extends CA.CellularAutomaton {

  constructor() {
    super({
      name:        'Rule 110',
      description: 'An elementary CA: 2 states, 3 neighbors, 8-entry lookup table. '
                 + 'Every cell is a pure function of the 3 cells above it.',
      blankState:  0,
      seedRows:    1,
      displayMode: 'grid',
    });
    // Lookup table for rule 110: index = L*4 + C*2 + R
    this._rule = [];
    let n = 110;
    for (let i = 0; i < 8; i++) {
      this._rule.push(n % 2);
      n = Math.floor(n / 2);
    }
  }

  suggestSize() { return { width: 80, height: 60 }; }

  initGrid(input) {
    if (typeof input === 'number' && input > 0) {
      const bits = CA.CellularAutomaton.toBitsLSB(input, this.width);
      for (let c = 0; c < this.width; c++) this.grid[0][this.width - 1 - c] = bits[c] || 0;
    } else {
      this.grid[0][this.width - 1] = 1;
    }
  }

  computeCell(r, c) {
    const L = this.get(r-1, c-1), C = this.get(r-1, c), R = this.get(r-1, c+1);
    return this._rule[L * 4 + C * 2 + R];
  }

  sourceCells(r, c) {
    if (r === 0) return [];
    return [{r: r-1, c: c-1}, {r: r-1, c: c}, {r: r-1, c: c+1}];
  }

  cellStyle(v) {
    return v === 1
      ? { text: '', colors: ['#58a6ff'], fg: '#000' }
      : { text: '', colors: ['#161b22'], fg: '#333' };
  }
};
