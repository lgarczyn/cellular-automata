"use strict";

// Collatz step on a hex grid display.
// Same 3x+1 / 2 logic, rendered as flat-top hexagons.

CA.CollatzHex = class CollatzHex extends CA.CollatzStep {

  constructor() {
    super({ displayMode: 'hexgrid' });
    this.name = '3x+1 / 2 (Hex)';
    this.description =
      'Hex layout: each cell touches its 3 inputs directly, '
    + 'making the neighborhood structure visible.';
  }
};
