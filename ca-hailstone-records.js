"use strict";

// Hailstone records: numbers whose Collatz total stopping time exceeds
// every smaller positive integer's (OEIS A006877). For each record n we
// run the 3x+1/2 cellular automaton and render two horizontal strips of
// CA cells: the input's binary digits (top), and the cell at the input's
// most-significant column sampled across every CA row (below). Cells are
// drawn with the CA's own styling so digit/carry markers are preserved.

CA.HailstoneRecords = {

  collatzLength(n) {
    let steps = 0;
    let v = n;
    while (v > 1) {
      v = v % 2 === 0 ? v / 2 : 3 * v + 1;
      steps++;
    }
    return steps;
  },

  computeRecords(limit) {
    const records = [];
    let best = -1;
    for (let n = 1; n <= limit; n++) {
      const steps = this.collatzLength(n);
      if (steps > best) {
        best = steps;
        records.push({ n, steps });
      }
    }
    return records;
  },

  bitLength(n) {
    return n <= 0 ? 1 : Math.floor(Math.log2(n)) + 1;
  },

  // Build a styled cell <span> from the CA grid at (r, c), matching the
  // CA's own cellStyle so digit/carry/LeastEdge appear consistent with
  // the larger 3x+1/2 visualization above.
  makeCell(ca, r, c) {
    const span = document.createElement('span');
    span.className = 'h-cell';
    const cell = ca.get(r, c);
    if (cell === null || cell === ca.blankState) {
      span.classList.add('h-cell-blank');
      return span;
    }
    const style = ca.cellStyle(cell, r, c);
    if (style.hidden) {
      span.classList.add('h-cell-blank');
      return span;
    }
    span.style.background = style.colors[0];
    span.style.color = style.fg || '#ccc';
    if (style.text) span.textContent = style.text;
    return span;
  },

  renderRecord(n, steps) {
    const ca = new CA.CollatzStep();
    const size = ca.suggestSize(n);
    ca.run(n, size.width, size.height);

    // Column index of the input's MSB in the CA grid:
    //   col 0 = LeastEdge, col 1 = bit 0 (LSB), ..., col bitLength = bit (bitLength-1) = MSB.
    const m = this.bitLength(n);

    const card = document.createElement('div');
    card.className = 'hailstone-record';

    const header = document.createElement('div');
    header.className = 'hailstone-record-header';
    const numSpan = document.createElement('span');
    numSpan.className = 'hailstone-num';
    numSpan.textContent = n;
    const stepsSpan = document.createElement('span');
    stepsSpan.className = 'hailstone-steps';
    stepsSpan.textContent = `${steps} steps`;
    header.appendChild(numSpan);
    header.appendChild(stepsSpan);
    card.appendChild(header);

    const rows = document.createElement('div');
    rows.className = 'hailstone-rows';

    // Row 1: input binary, MSB on the left → LSB on the right.
    const binaryRow = document.createElement('div');
    binaryRow.className = 'hailstone-row';
    const binaryLabel = document.createElement('span');
    binaryLabel.className = 'h-row-label';
    binaryLabel.textContent = 'bin';
    binaryRow.appendChild(binaryLabel);
    for (let c = m; c >= 1; c--) {
      binaryRow.appendChild(this.makeCell(ca, 0, c));
    }
    rows.appendChild(binaryRow);

    // Row 2: column at the input's MSB position, sampled across every CA row,
    // laid out horizontally (step 0 on the left → final step on the right).
    const colRow = document.createElement('div');
    colRow.className = 'hailstone-row';
    const colLabel = document.createElement('span');
    colLabel.className = 'h-row-label';
    colLabel.textContent = 'col';
    colRow.appendChild(colLabel);
    for (let r = 0; r < ca.height; r++) {
      colRow.appendChild(this.makeCell(ca, r, m));
    }
    rows.appendChild(colRow);

    card.appendChild(rows);
    return card;
  },

  render(container, limit = 100000) {
    const records = this.computeRecords(limit);

    const section = document.createElement('section');
    section.id = 'hailstone-records';
    section.className = 'ca-section';

    const h2 = document.createElement('h2');
    h2.textContent = 'Hailstone Records';
    section.appendChild(h2);

    const desc = document.createElement('p');
    desc.className = 'desc';
    desc.textContent =
      `Numbers up to ${limit.toLocaleString()} whose Collatz total stopping time `
    + `exceeds every smaller integer's (OEIS A006877, computed at startup). `
    + `For each, the top strip is the input in binary (MSB on the left); the `
    + `strip below is the cell at the input's most-significant column, sampled `
    + `across every row of the 3x+1/2 cellular automaton — digit/carry marks `
    + `come straight from the CA's own styling.`;
    section.appendChild(desc);

    const list = document.createElement('div');
    list.className = 'hailstone-list';
    for (const { n, steps } of records) {
      list.appendChild(this.renderRecord(n, steps));
    }
    section.appendChild(list);

    container.appendChild(section);
  }
};
