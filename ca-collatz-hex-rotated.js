"use strict";

// Collatz step on a remapped hex grid.
// Columns slide up, producing a vertical flow.

CA.CollatzHexRotated = class CollatzHexRotated extends CA.CollatzStep {

  constructor() {
    super({ displayMode: 'hexgrid-rotated' });
    this.name = '3x+1 / 2 (Hex Rotated)';
    this.description =
      'Rotated hex view: columns slide up so the 3 inputs sit directly above each cell.';
  }
};
