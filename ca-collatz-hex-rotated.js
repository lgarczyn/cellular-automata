"use strict";

// Collatz step on a remapped hex grid.
// Columns slide up, producing a vertical flow.

CA.CollatzHexRotated = class CollatzHexRotated extends CA.CollatzStep {

  constructor() {
    super({ displayMode: 'hexgrid-rotated' });
    this.name = '3x+1 / 2 (Hex Rotated)';
    this.description =
      'Collatz step on a hexagonal grid where each column slides one cell up '
    + 'relative to its left neighbor, producing a downward flow.';
  }
};
