"use strict";

window.CA = window.CA || {};

CA.LEAST_EDGE = Object.freeze({ type: 'LeastEdge', digit: 0, carry: 1 });

CA.CellularAutomaton = class CellularAutomaton {

  constructor({
    name         = 'Untitled',
    description  = '',
    blankState   = null,
    seedRows     = 1,
    displayMode  = 'grid',
    hexGroupSize = 4,
  } = {}) {
    this.name        = name;
    this.description = description;
    this.blankState  = blankState;
    this.seedRows    = seedRows;
    this.displayMode = displayMode;
    this.hexGroupSize = hexGroupSize;
    this.grid   = [];
    this.width  = 0;
    this.height = 0;
  }

  get(r, c) {
    if (r < 0 || r >= this.height || c < 0 || c >= this.width) return this.blankState;
    return this.grid[r][c];
  }

  set(r, c, value) {
    if (r >= 0 && r < this.height && c >= 0 && c < this.width) this.grid[r][c] = value;
  }

  allocate(width, height) {
    this.width  = width;
    this.height = height;
    this.grid   = Array.from({ length: height }, () => new Array(width).fill(this.blankState));
  }

  // Override in subclasses
  initGrid(input) {}
  computeCell(r, c) { return this.blankState; }
  cellStyle(value)  { return { text: String(value), colors: ['#1a1e24'], fg: '#888' }; }
  readRow(r)        { return null; }
  suggestSize()     { return { width: 40, height: 40 }; }
  sourceCells(r, c) { return []; }

  allSourceCells(r, c) {
    const visited = new Set();
    const queue = [{r, c}];
    const result = [];
    while (queue.length > 0) {
      const {r: cr, c: cc} = queue.shift();
      const key = `${cr},${cc}`;
      if (visited.has(key)) continue;
      visited.add(key);
      for (const src of this.sourceCells(cr, cc)) {
        const sk = `${src.r},${src.c}`;
        if (src.r >= 0 && src.r < this.height && src.c >= 0 && src.c < this.width && !visited.has(sk)) {
          result.push(src);
          queue.push(src);
        }
      }
    }
    return result;
  }

  run(input, width, height) {
    const size = this.suggestSize(input);
    this.allocate(width ?? size.width, height ?? size.height);
    this.initGrid(input);
    for (let r = this.seedRows; r < this.height; r++) this.computeRow(r);
    return this.grid;
  }

  computeRow(r) {
    for (let c = 0; c < this.width; c++) this.grid[r][c] = this.computeCell(r, c);
  }

  trimmedGrid() {
    let maxCol = 0;
    for (const row of this.grid) {
      for (let c = row.length - 1; c >= 0; c--) {
        if (row[c] !== this.blankState) { maxCol = Math.max(maxCol, c); break; }
      }
    }
    const w = maxCol + 2;
    return this.grid.map(row => row.slice(0, Math.min(row.length, w)));
  }

  // Number ↔ bit-array utilities (no bitwise ops)
  static toBitsMSB(n, len) {
    const bits = [];
    let v = n;
    while (v > 0) { bits.unshift(v % 2); v = Math.floor(v / 2); }
    while (bits.length < len) bits.unshift(0);
    return bits;
  }

  static toBitsLSB(n, len) {
    const bits = [];
    let v = n;
    while (v > 0) { bits.push(v % 2); v = Math.floor(v / 2); }
    while (bits.length < len) bits.push(0);
    return bits;
  }

  static bitLength(n) { return n <= 0 ? 1 : Math.ceil(Math.log2(n + 1)); }
};
