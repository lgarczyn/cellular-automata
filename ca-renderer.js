"use strict";

CA.Renderer = class Renderer {

  constructor(container, automaton) {
    this.container = container;
    this.automaton = automaton;
  }

  render(opts = {}) {
    // Clean up any tooltip elements from a previous render — they live on
    // document.body and don't follow the redrawn table/SVG, so they would
    // otherwise stay visible after a re-render (e.g. after a row-0 toggle).
    for (const el of document.querySelectorAll('.ca-tooltip')) el.remove();
    const mode = this.automaton.displayMode;
    if (mode === 'hexgrid-rotated') this._renderHexGridRotated(opts);
    else if (mode === 'hexgrid')    this._renderHexGrid(opts);
    else if (mode === 'hex')        this._renderHex(opts);
    else                            this._renderGrid(opts);
  }

  // ── Square grid (table) ──────────────────────────────────────────
  //
  // Each grid row becomes a <tr> with this column layout:
  //   [leftSpacer] [extension?] [label] [data cells] [value] [rightSpacer]
  //   ─ leftSpacer absorbs blank columns above the row's leftmost non-blank.
  //   ─ extension is a "+" cell on row 0 only when onCellClick is set, used
  //     to grow the input by one bit on click.
  //   ─ label / value are the row-index and readRow(r) readout.
  //   ─ data cells are rendered MSB-first (last column first), with runs of
  //     blank/hidden cells merged into single colspan'd spacers.

  _renderGrid({ cellSize = 28, showRowLabels = true, showValues = false, trimBlanks = true, onCellClick = null } = {}) {
    const a     = this.automaton;
    const grid  = trimBlanks ? a.trimmedGrid() : a.grid;
    const blank = a.blankState;
    this.container.style.setProperty('--cell-size', cellSize + 'px');

    // ── small builders ────────────────────────────────────────────────
    const cellMap = new Map();
    const spacer = (colSpan) => {
      const td = document.createElement('td');
      td.colSpan = colSpan;
      return td;
    };
    const isInvisibleCell = (v, r, c) => {
      if (v === null || v === blank) return true;
      return a.cellStyle(v, r, c).hidden === true;
    };
    const makeDataTD = (v, r, c) => {
      const td = this._makeTD(v, a, r, c);
      td.dataset.row = r;
      td.dataset.col = c;
      cellMap.set(`${r},${c}`, td);
      return td;
    };
    const makeExtensionTD = (col) => {
      const td = document.createElement('td');
      td.className = 'cell-extend';
      td.textContent = '+';
      td.dataset.row = 0;
      td.dataset.col = col;
      td.dataset.extend = '1';
      return td;
    };
    const makeLabelTD = (r) => {
      const td = document.createElement('td');
      if (showRowLabels) { td.textContent = r; td.className = 'row-label'; }
      return td;
    };
    const makeValueTD = (r) => {
      const td = document.createElement('td');
      if (showValues) {
        td.className = 'row-value';
        const span = document.createElement('span');
        span.className = 'value-text';
        span.textContent = a.readRow(r);
        td.appendChild(span);
      }
      return td;
    };

    // ── per-row layout ────────────────────────────────────────────────
    const buildRow = (r, row) => {
      const len = row.length;
      // Find first and last visible column.
      let first = len, last = -1;
      for (let c = 0; c < len; c++) {
        if (isInvisibleCell(row[c], r, c)) continue;
        if (c < first) first = c;
        last = c;
      }

      const tr = document.createElement('tr');
      if (first > last) {
        // Entirely blank row.
        tr.appendChild(spacer(len + 2));
        return tr;
      }

      // Row 0 may steal one column from the left spacer for the "+" cell.
      const wantExtend = onCellClick && r === 0 && (len - 1 - last) >= 1;
      const leadBlanks = (len - 1 - last) - (wantExtend ? 1 : 0);

      if (leadBlanks > 0)        tr.appendChild(spacer(leadBlanks));
      if (wantExtend)            tr.appendChild(makeExtensionTD(last + 1));
                                 tr.appendChild(makeLabelTD(r));

      // Data cells, MSB-first; runs of blanks/hidden merge into spacers.
      let c = last;
      while (c >= first) {
        if (isInvisibleCell(row[c], r, c)) {
          const start = c;
          while (c >= first && isInvisibleCell(row[c], r, c)) c--;
          tr.appendChild(spacer(start - c));
        } else {
          tr.appendChild(makeDataTD(row[c], r, c));
          c--;
        }
      }

                                 tr.appendChild(makeValueTD(r));
      if (first > 0)             tr.appendChild(spacer(first));
      return tr;
    };

    // ── assemble table ────────────────────────────────────────────────
    const tbl = document.createElement('table');
    if (onCellClick) tbl.classList.add('grid-clickable');
    for (let r = 0; r < grid.length; r++) tbl.appendChild(buildRow(r, grid[r]));

    // ── interaction wiring ────────────────────────────────────────────
    if (onCellClick) {
      tbl.addEventListener('click', e => {
        const td = e.target.closest('td[data-row]');
        if (!td) return;
        const r = parseInt(td.dataset.row);
        if (r !== 0) return;
        onCellClick(r, parseInt(td.dataset.col));
      });
    }
    this._attachGridHover(tbl, cellMap, a);
    this._attachTooltip(tbl, '[data-row]', el => {
      if (el.dataset.extend) return 'click to add a leading 1';
      const r = parseInt(el.dataset.row);
      const bitIdx = a.bitColToIndex(parseInt(el.dataset.col));
      const bitTip = (r === 0 && onCellClick && bitIdx !== null) ? `bit ${bitIdx} — click to toggle` : '';
      const rowTip = this._tooltipText(r, showRowLabels, showValues ? a.readRow(r) : null);
      return [bitTip, rowTip].filter(Boolean).join('  ');
    });

    this.container.innerHTML = '';
    this.container.appendChild(tbl);
  }

  // ── Nibble-grouped hex digits (table) ────────────────────────────

  _renderHex({ cellSize = 36, showRowLabels = true, showValues = false, trimBlanks = true } = {}) {
    const a    = this.automaton;
    const grid = trimBlanks ? a.trimmedGrid() : a.grid;
    const gsz  = a.hexGroupSize;
    const blank = a.blankState;
    this.container.style.setProperty('--cell-size', cellSize + 'px');

    const tbl = document.createElement('table');
    for (let r = 0; r < grid.length; r++) {
      const tr = document.createElement('tr');
      tr.dataset.row = r;

      const nibbleTDs = [];
      for (let i = 0; i < grid[r].length; i += gsz) {
        let nibble = 0, allBlank = true, power = 1;
        for (let b = 0; b < gsz && (i + b) < grid[r].length; b++) {
          const cell = grid[r][i + b];
          if (cell !== blank) {
            allBlank = false;
            const d = typeof cell === 'object' ? (cell.digit ?? 0) : cell;
            nibble += d * power;
          }
          power *= 2;
        }
        const td = document.createElement('td');
        if (allBlank) {
          td.style.background = '#0d1117';
          td.style.color = '#333';
        } else {
          const s = this._nibbleStyle(nibble);
          td.style.background = s.bg;
          td.style.color = s.fg;
          td.textContent = nibble.toString(16).toUpperCase();
        }
        nibbleTDs.push(td);
      }
      for (let i = nibbleTDs.length - 1; i >= 0; i--) tr.appendChild(nibbleTDs[i]);

      tbl.appendChild(tr);
    }

    this._attachTooltip(tbl, 'tr[data-row]', el => {
      const r = parseInt(el.dataset.row);
      return this._tooltipText(r, showRowLabels, showValues ? a.readRow(r) : null);
    });

    this.container.innerHTML = '';
    this.container.appendChild(tbl);
  }

  // ── Flat-top hexagonal grid (SVG) ───────────────────────────────

  _renderHexGrid({ cellSize = 24, showRowLabels = true, showValues = false, trimBlanks = true, onCellClick = null } = {}) {
    const a    = this.automaton;
    const grid = trimBlanks ? a.trimmedGrid() : a.grid;

    const R       = cellSize / 2;
    const drawR   = R - 2;               // smaller for 4px gap
    const sqrt3   = Math.sqrt(3);
    const hexW    = sqrt3 * R;            // pointy-top hex width (spacing)

    const numRows = grid.length;
    const numCols = grid[0]?.length ?? 0;

    const labelPad = showRowLabels ? 30 : 0;
    const valuePad = showValues ? 60 : 0;
    const padX   = hexW / 2 + 8 + labelPad;
    const padY   = R + 2;

    const svgW = padX + (numCols - 1) * hexW + (numRows - 1) * hexW / 2 + hexW / 2 + 8 + valuePad;
    const svgH = padY + (numRows - 1) * 1.5 * R + R + 4;

    const NS  = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', svgW);
    svg.setAttribute('height', svgH);
    svg.style.display = 'block';

    const style = document.createElementNS(NS, 'style');
    style.textContent = '.hex-row:hover polygon { filter: brightness(1.2); }';
    svg.appendChild(style);

    const fontSize = Math.max(7, R * 0.7);
    const defaultStroke = '#21262d';
    const polyMap = new Map();

    for (let r = 0; r < numRows; r++) {
      const g = document.createElementNS(NS, 'g');
      g.setAttribute('class', 'hex-row');

      const cy = padY + r * 1.5 * R;
      let minCx = Infinity, maxCx = -Infinity;

      for (let c = grid[r].length - 1; c >= 0; c--) {
        const dc = grid[r].length - 1 - c;
        const cx = padX + dc * hexW + r * hexW / 2;

        const cell  = grid[r][c];
        if (cell === null || cell === a.blankState) continue;
        const cs    = a.cellStyle(cell, r, c);
        if (cs.hidden) continue;

        if (cx < minCx) minCx = cx;
        if (cx > maxCx) maxCx = cx;

        const poly = document.createElementNS(NS, 'polygon');
        poly.setAttribute('points', this._hexPoints(cx, cy, drawR));
        poly.setAttribute('fill', cs.colors[0]);
        poly.setAttribute('stroke', defaultStroke);
        poly.setAttribute('stroke-width', '1');
        poly.dataset.row = r;
        poly.dataset.col = c;
        polyMap.set(`${r},${c}`, poly);
        g.appendChild(poly);

        if (cs.text) {
          const txt = document.createElementNS(NS, 'text');
          txt.setAttribute('x', cx);
          txt.setAttribute('y', cy + fontSize * 0.35);
          txt.setAttribute('text-anchor', 'middle');
          txt.setAttribute('fill', cs.fg || '#ccc');
          txt.setAttribute('font-size', fontSize);
          txt.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
          txt.setAttribute('pointer-events', 'none');
          txt.textContent = cs.text;
          g.appendChild(txt);
        }
      }

      // Row label — LEFT of leftmost data cell
      if (showRowLabels && minCx < Infinity) {
        const lbl = document.createElementNS(NS, 'text');
        lbl.setAttribute('x', minCx - R - 4);
        lbl.setAttribute('y', cy + fontSize * 0.35);
        lbl.setAttribute('text-anchor', 'end');
        lbl.setAttribute('fill', '#8b949e');
        lbl.setAttribute('font-size', fontSize);
        lbl.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
        lbl.setAttribute('pointer-events', 'none');
        lbl.textContent = r;
        g.appendChild(lbl);
      }

      // Row value — RIGHT of rightmost data cell
      if (showValues && maxCx > -Infinity) {
        const val = document.createElementNS(NS, 'text');
        val.setAttribute('x', maxCx + R + 4);
        val.setAttribute('y', cy + fontSize * 0.35);
        val.setAttribute('text-anchor', 'start');
        val.setAttribute('fill', '#3fb950');
        val.setAttribute('font-size', fontSize);
        val.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
        val.setAttribute('pointer-events', 'none');
        val.textContent = a.readRow(r);
        g.appendChild(val);
      }

      svg.appendChild(g);
    }

    this._wireHexClick(svg, polyMap, grid, a, onCellClick, NS, fontSize, drawR, (col0Last) => {
      // Pointy-top: extension hex sits at row 0, "would be" col col0Last+1.
      const dc = grid[0].length - 1 - (col0Last + 1);
      return { cx: padX + dc * hexW + 0 * hexW / 2, cy: padY };
    }, (cx, cy, R) => this._hexPoints(cx, cy, R));

    this._attachHexHover(svg, polyMap, a, NS);
    this._attachTooltip(svg, 'polygon[data-row]', el => {
      const r = parseInt(el.dataset.row);
      if (el.dataset.extend) return 'click to add a leading 1';
      const bitIdx = a.bitColToIndex(parseInt(el.dataset.col));
      const bitTip = (r === 0 && onCellClick && bitIdx !== null) ? `bit ${bitIdx} — click to toggle` : '';
      const rowTip = this._tooltipText(r, showRowLabels, showValues ? a.readRow(r) : null);
      return [bitTip, rowTip].filter(Boolean).join('  ');
    });

    this.container.innerHTML = '';
    this.container.appendChild(svg);
  }

  // ── Rotated hex grid ────────────────────────────────────────────
  // Columns slide one cell up relative to left neighbor; flat-top hexagons;
  // rows offset half a cell right.

  _renderHexGridRotated({ cellSize = 24, showRowLabels = true, showValues = false, trimBlanks = true, onCellClick = null } = {}) {
    const a    = this.automaton;
    const grid = trimBlanks ? a.trimmedGrid() : a.grid;

    const R       = cellSize / 2;
    const drawR   = R - 2;
    const sqrt3   = Math.sqrt(3);
    // Flat-top hex: width = 2R, height = sqrt3 * R
    const hexH    = sqrt3 * R;
    const colStep = 1.5 * R;            // horizontal distance between columns
    const rowStep = hexH / 2;           // vertical offset per row (half hex height)

    const numRows = grid.length;
    const numCols = grid[0]?.length ?? 0;

    const labelPad = showRowLabels ? 30 : 0;
    const valuePad = showValues ? 60 : 0;
    const padX   = R + 8 + labelPad;
    const padY   = hexH / 2 + 8;

    const maxSlide = Math.max(0, numCols - 1);
    const svgW = padX + (numCols - 1) * colStep + (numRows - 1) * colStep + R + 8 + valuePad;
    const svgH = padY + (numRows - 1) * rowStep + maxSlide * rowStep + hexH / 2 + 4;

    const NS  = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', svgW);
    svg.setAttribute('height', svgH);
    svg.style.display = 'block';

    const style = document.createElementNS(NS, 'style');
    style.textContent = '.hex-row:hover polygon { filter: brightness(1.2); }';
    svg.appendChild(style);

    const fontSize = Math.max(7, R * 0.7);
    const defaultStroke = '#21262d';
    const polyMap = new Map();

    for (let r = 0; r < numRows; r++) {
      const g = document.createElementNS(NS, 'g');
      g.setAttribute('class', 'hex-row');

      let minCx = Infinity, minCy = 0, maxCx = -Infinity, maxCy = 0;
      for (let c = grid[r].length - 1; c >= 0; c--) {
        const cell = grid[r][c];
        if (cell === null || cell === a.blankState) continue;
        const cs = a.cellStyle(cell, r, c);
        if (cs.hidden) continue;

        const dc = grid[r].length - 1 - c;
        const cx = padX + dc * colStep + r * colStep;
        const cy = padY + (r + (numCols - 1 - dc)) * rowStep;

        if (cx < minCx) { minCx = cx; minCy = cy; }
        if (cx > maxCx) { maxCx = cx; maxCy = cy; }

        const poly = document.createElementNS(NS, 'polygon');
        poly.setAttribute('points', this._hexPointsFlat(cx, cy, drawR));
        poly.setAttribute('fill', cs.colors[0]);
        poly.setAttribute('stroke', defaultStroke);
        poly.setAttribute('stroke-width', '1');
        poly.dataset.row = r;
        poly.dataset.col = c;
        polyMap.set(`${r},${c}`, poly);
        g.appendChild(poly);

        if (cs.text) {
          const txt = document.createElementNS(NS, 'text');
          txt.setAttribute('x', cx);
          txt.setAttribute('y', cy + fontSize * 0.35);
          txt.setAttribute('text-anchor', 'middle');
          txt.setAttribute('fill', cs.fg || '#ccc');
          txt.setAttribute('font-size', fontSize);
          txt.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
          txt.setAttribute('pointer-events', 'none');
          txt.textContent = cs.text;
          g.appendChild(txt);
        }
      }

      // Row label — LEFT of leftmost data cell
      if (showRowLabels && minCx < Infinity) {
        const lbl = document.createElementNS(NS, 'text');
        lbl.setAttribute('x', minCx - R - 4);
        lbl.setAttribute('y', minCy + fontSize * 0.35);
        lbl.setAttribute('text-anchor', 'end');
        lbl.setAttribute('fill', '#8b949e');
        lbl.setAttribute('font-size', fontSize);
        lbl.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
        lbl.setAttribute('pointer-events', 'none');
        lbl.textContent = r;
        g.appendChild(lbl);
      }

      // Row value — RIGHT of rightmost data cell
      if (showValues && maxCx > -Infinity) {
        const val = document.createElementNS(NS, 'text');
        val.setAttribute('x', maxCx + R + 4);
        val.setAttribute('y', maxCy + fontSize * 0.35);
        val.setAttribute('text-anchor', 'start');
        val.setAttribute('fill', '#3fb950');
        val.setAttribute('font-size', fontSize);
        val.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
        val.setAttribute('pointer-events', 'none');
        val.textContent = a.readRow(r);
        g.appendChild(val);
      }

      svg.appendChild(g);
    }

    this._wireHexClick(svg, polyMap, grid, a, onCellClick, NS, fontSize, drawR, (col0Last) => {
      // Rotated: same row-0 placement scheme.
      const dc = grid[0].length - 1 - (col0Last + 1);
      return {
        cx: padX + dc * colStep + 0 * colStep,
        cy: padY + (0 + (numCols - 1 - dc)) * rowStep,
      };
    }, (cx, cy, R) => this._hexPointsFlat(cx, cy, R));

    this._attachHexHover(svg, polyMap, a, NS);
    this._attachTooltip(svg, 'polygon[data-row]', el => {
      const r = parseInt(el.dataset.row);
      if (el.dataset.extend) return 'click to add a leading 1';
      const bitIdx = a.bitColToIndex(parseInt(el.dataset.col));
      const bitTip = (r === 0 && onCellClick && bitIdx !== null) ? `bit ${bitIdx} — click to toggle` : '';
      const rowTip = this._tooltipText(r, showRowLabels, showValues ? a.readRow(r) : null);
      return [bitTip, rowTip].filter(Boolean).join('  ');
    });

    this.container.innerHTML = '';
    this.container.appendChild(svg);
  }

  // Common click + extension-cell wiring for both hex SVG renderers.
  _wireHexClick(svg, polyMap, grid, a, onCellClick, NS, fontSize, drawR, posFn, pointsFn) {
    if (!onCellClick) return;
    let row0Last = -1;
    for (let c = grid[0]?.length - 1 ?? -1; c >= 0; c--) {
      const cell = grid[0][c];
      if (cell === null || cell === a.blankState) continue;
      const cs = a.cellStyle(cell, 0, c);
      if (cs.hidden) continue;
      row0Last = c;
      break;
    }
    if (row0Last !== -1 && row0Last < grid[0].length - 1) {
      const { cx, cy } = posFn(row0Last);
      const ext = document.createElementNS(NS, 'polygon');
      ext.setAttribute('points', pointsFn(cx, cy, drawR));
      ext.setAttribute('fill', 'transparent');
      ext.setAttribute('stroke', '#8b949e');
      ext.setAttribute('stroke-width', '1');
      ext.setAttribute('stroke-dasharray', '3 2');
      ext.dataset.row = 0;
      ext.dataset.col = row0Last + 1;
      ext.dataset.extend = '1';
      ext.style.cursor = 'pointer';
      const txt = document.createElementNS(NS, 'text');
      txt.setAttribute('x', cx);
      txt.setAttribute('y', cy + fontSize * 0.35);
      txt.setAttribute('text-anchor', 'middle');
      txt.setAttribute('fill', '#8b949e');
      txt.setAttribute('font-size', fontSize);
      txt.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
      txt.setAttribute('pointer-events', 'none');
      txt.textContent = '+';
      svg.appendChild(ext);
      svg.appendChild(txt);
    }
    svg.addEventListener('click', e => {
      const poly = e.target.closest('polygon[data-row]');
      if (!poly) return;
      const tr = parseInt(poly.dataset.row);
      if (tr !== 0) return;
      const tc = parseInt(poly.dataset.col);
      onCellClick(tr, tc);
    });
    for (const [key, poly] of polyMap) {
      if (key.startsWith('0,')) poly.style.cursor = 'pointer';
    }
  }

  // Pointy-top hexagon vertex string for SVG polygon
  _hexPoints(cx, cy, R) {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const angle = Math.PI / 6 + Math.PI / 3 * i;  // pointy-top: start at 30°
      pts.push(`${(cx + R * Math.cos(angle)).toFixed(1)},${(cy + R * Math.sin(angle)).toFixed(1)}`);
    }
    return pts.join(' ');
  }

  // Flat-top hexagon vertex string for SVG polygon
  _hexPointsFlat(cx, cy, R) {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const angle = Math.PI / 3 * i;  // flat-top: start at 0°
      pts.push(`${(cx + R * Math.cos(angle)).toFixed(1)},${(cy + R * Math.sin(angle)).toFixed(1)}`);
    }
    return pts.join(' ');
  }

  // ── Hover source-cell highlighting ─────────────────────────────

  _attachGridHover(tbl, cellMap, a) {
    let highlighted = [];
    tbl.addEventListener('mouseover', e => {
      for (const el of highlighted) el.classList.remove('source-highlight', 'hovered-cell');
      highlighted = [];
      const td = e.target.closest('td[data-row]');
      if (!td) return;
      const r = parseInt(td.dataset.row), c = parseInt(td.dataset.col);
      td.classList.add('hovered-cell');
      highlighted.push(td);
      for (const src of a.sourceCells(r, c)) {
        if (src.r >= 0 && src.r < a.height && src.c >= 0 && src.c < a.width) {
          const el = cellMap.get(`${src.r},${src.c}`);
          if (el) { el.classList.add('source-highlight'); highlighted.push(el); }
        }
      }
    });
    tbl.addEventListener('mouseleave', () => {
      for (const el of highlighted) el.classList.remove('source-highlight', 'hovered-cell');
      highlighted = [];
    });
  }

  _attachHexHover(svg, polyMap, a, NS) {
    let highlighted = [];
    const highlightStroke = '#58a6ff';
    const hoveredStroke = '#f0883e';

    svg.addEventListener('mouseover', e => {
      const poly = e.target.closest('polygon[data-row]');
      // Clear previous
      for (const {el, origStroke, origWidth} of highlighted) {
        el.setAttribute('stroke', origStroke);
        el.setAttribute('stroke-width', origWidth);
      }
      highlighted = [];
      if (!poly) return;
      const r = parseInt(poly.dataset.row), c = parseInt(poly.dataset.col);
      // Highlight hovered cell
      highlighted.push({el: poly, origStroke: poly.getAttribute('stroke'), origWidth: poly.getAttribute('stroke-width')});
      poly.setAttribute('stroke', hoveredStroke);
      poly.setAttribute('stroke-width', '3');
      // Highlight sources
      for (const src of a.sourceCells(r, c)) {
        if (src.r >= 0 && src.r < a.height && src.c >= 0 && src.c < a.width) {
          const el = polyMap.get(`${src.r},${src.c}`);
          if (el) {
            highlighted.push({el, origStroke: el.getAttribute('stroke'), origWidth: el.getAttribute('stroke-width')});
            el.setAttribute('stroke', highlightStroke);
            el.setAttribute('stroke-width', '2.5');
          }
        }
      }
    });
    svg.addEventListener('mouseleave', () => {
      for (const {el, origStroke, origWidth} of highlighted) {
        el.setAttribute('stroke', origStroke);
        el.setAttribute('stroke-width', origWidth);
      }
      highlighted = [];
    });
  }

  // ── Shared helpers ──────────────────────────────────────────────

  _tooltipText(row, showRow, value) {
    const parts = [];
    if (showRow) parts.push(`row ${row}`);
    if (value !== null && value !== undefined) parts.push(`= ${value}`);
    return parts.join('  ');
  }

  _attachTooltip(root, selector, textFn) {
    let tip = null;
    const show = (e) => {
      const el = e.target.closest(selector);
      if (!el) { hide(); return; }
      const text = textFn(el);
      if (!text) { hide(); return; }
      if (!tip) {
        tip = document.createElement('div');
        tip.className = 'ca-tooltip';
        document.body.appendChild(tip);
      }
      tip.textContent = text;
      tip.style.left = (e.clientX + 12) + 'px';
      tip.style.top  = (e.clientY - 8) + 'px';
      tip.style.display = '';
    };
    const hide = () => {
      if (tip) tip.style.display = 'none';
    };
    const move = (e) => {
      if (tip && tip.style.display !== 'none') {
        tip.style.left = (e.clientX + 12) + 'px';
        tip.style.top  = (e.clientY - 8) + 'px';
      }
      show(e);
    };
    root.addEventListener('mousemove', move);
    root.addEventListener('mouseleave', hide);
  }

  _makeTD(value, automaton, r, c) {
    const td = document.createElement('td');
    if (value === null || value === automaton.blankState) return td;

    const style = automaton.cellStyle(value, r, c);
    const colors = style.colors;

    if (colors.length === 1) {
      td.style.background = colors[0];
    } else if (colors.length === 2) {
      td.style.background = `linear-gradient(135deg, ${colors[0]} 50%, ${colors[1]} 50%)`;
    } else {
      const stops = colors.map((c, i) =>
        `${c} ${(i / colors.length * 100).toFixed(1)}%, ${c} ${((i + 1) / colors.length * 100).toFixed(1)}%`
      ).join(', ');
      td.style.background = `linear-gradient(135deg, ${stops})`;
    }

    td.style.color = style.fg || this._autoFG(colors[0]);
    if (style.text) td.textContent = style.text;
    return td;
  }

  _nibbleStyle(nibble) {
    const hue = (nibble / 16) * 300;
    return { bg: `hsl(${hue}, 55%, 25%)`, fg: `hsl(${hue}, 60%, 80%)` };
  }

  _autoFG(hex) {
    if (!hex || !hex.startsWith('#') || hex.length < 7) return '#ccc';
    const r = parseInt(hex.substr(1, 2), 16);
    const g = parseInt(hex.substr(3, 2), 16);
    const b = parseInt(hex.substr(5, 2), 16);
    return (r * 299 + g * 587 + b * 114) / 1000 > 140 ? '#000' : '#fff';
  }
};
