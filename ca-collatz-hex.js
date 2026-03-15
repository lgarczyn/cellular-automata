"use strict";

// Collatz step on a hex grid display.
// Same 3x+1 / 2 logic, rendered as flat-top hexagons.

CA.CollatzHex = class CollatzHex extends CA.CollatzStep {

  constructor() {
    super({ displayMode: 'hexgrid' });
    this.name = '3x+1 / 2 (Hex)';
    this.description =
      'Collatz step displayed on a hexagonal grid. '
    + 'Each cell has 3 upper neighbors matching the 3 inputs: shifted, same, carry.';
  }
};
