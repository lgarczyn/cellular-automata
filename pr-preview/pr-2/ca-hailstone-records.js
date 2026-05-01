"use strict";

// Hailstone records: numbers whose Collatz total stopping time exceeds
// every smaller positive integer's (OEIS A006877). For each record n we
// render the input's binary digits as a row, and the bit at the input's
// most-significant position as the Collatz sequence iterates downward.

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

  collatzSequence(n) {
    const seq = [n];
    let v = n;
    while (v > 1) {
      v = v % 2 === 0 ? v / 2 : 3 * v + 1;
      seq.push(v);
    }
    return seq;
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

  bitAt(v, pos) {
    return Math.floor(v / Math.pow(2, pos)) % 2;
  },

  toBitsLSB(n) {
    const bits = [];
    let v = n;
    while (v > 0) {
      bits.push(v % 2);
      v = Math.floor(v / 2);
    }
    if (bits.length === 0) bits.push(0);
    return bits;
  },

  renderRecord(n, steps) {
    const seq = this.collatzSequence(n);
    const m = this.bitLength(n) - 1;
    const inputBits = this.toBitsLSB(n);

    const rows = new Array(seq.length);
    for (let r = 0; r < seq.length; r++) {
      const cells = [`<td class="row-label">${r}</td>`];
      for (let bp = m; bp >= 0; bp--) {
        if (r === 0) {
          const bit = bp < inputBits.length ? inputBits[bp] : 0;
          cells.push(`<td class="bit-${bit}">${bit}</td>`);
        } else if (bp === m) {
          const bit = this.bitAt(seq[r], bp);
          cells.push(`<td class="bit-${bit}">${bit}</td>`);
        } else {
          cells.push('<td class="bit-empty"></td>');
        }
      }
      cells.push(`<td class="row-value">${seq[r]}</td>`);
      rows[r] = '<tr>' + cells.join('') + '</tr>';
    }

    const card = document.createElement('div');
    card.className = 'hailstone-record';
    card.innerHTML =
      `<div class="hailstone-record-header">`
    +   `<span class="hailstone-num">${n}</span>`
    +   `<span class="hailstone-steps">${steps} steps</span>`
    + `</div>`
    + `<div class="hailstone-grid-wrap">`
    +   `<table class="hailstone-grid">${rows.join('')}</table>`
    + `</div>`;
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
    + `Each card's top row is the input in binary (MSB on the left); the column `
    + `below tracks the bit at the input's most-significant position as the `
    + `Collatz sequence runs, with the value at each step shown alongside.`;
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
