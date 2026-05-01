"use strict";

CA.Renderer = class Renderer {

  constructor(container, automaton) {
    this.container = container;
    this.automaton = automaton;
  }

  render(opts = {}) {
    const mode = this.automaton.displayMode;
    if (mode === 'hexgrid-rotated') this._renderHexGridRotated(opts);
    else if (mode === 'hexgrid')    this._renderHexGrid(opts);
    else if (mode === 'hex')        this._renderHex(opts);
    else                            this._renderGrid(opts);
  }

  // ── Square grid (table) ──────────────────────────────────────────

  _renderGrid({ cellSize = 28, showRowLabels = true, showValues = false, trimBlanks = true } = {}) {
    const a    = this.automaton;
    const grid = trimBlanks ? a.trimmedGrid() : a.grid;
    this.container.style.setProperty('--cell-size', cellSize + 'px');

    const cellMap = new Map();
    const blank = a.blankState;
    const tbl = document.createElement('table');
    for (let r = 0; r < grid.length; r++) {
      const row = grid[r];
      const len = row.length;
      // Find first and last visible column
      let first = len, last = -1;
      for (let c = 0; c < len; c++) {
        const v = row[c];
        if (v === null || v === blank) continue;
        const cs = a.cellStyle(v, r, c);
        if (cs.hidden) continue;
        if (c < first) first = c;
        last = c;
      }
      // Every row has len+2 columns: [spacer?] [label:1] [data] [value:1] [spacer?]
      const tr = document.createElement('tr');
      if (first > last) {
        const sp = document.createElement('td');
        sp.colSpan = len + 2;
        tr.appendChild(sp);
      } else {
        const leadBlanks = len - 1 - last;
        // Left spacer
        if (leadBlanks > 0) {
          const sp = document.createElement('td');
          sp.colSpan = leadBlanks;
          tr.appendChild(sp);
        }
        // Row label (1 col, adjacent to data)
        const lbl = document.createElement('td');
        if (showRowLabels) { lbl.textContent = r; lbl.className = 'row-label'; }
        tr.appendChild(lbl);
        // Actual cells — skip hidden cells, merge them into spacers
        let c = last;
        while (c >= first) {
          const v = row[c];
          const isBlank = v === null || v === blank;
          const isHidden = !isBlank && a.cellStyle(v, r, c).hidden;
          if (isBlank || isHidden) {
            // Count consecutive blank/hidden cells for colspan
            let span = 1;
            c--;
            while (c >= first) {
              const v2 = row[c];
              const b2 = v2 === null || v2 === blank;
              const h2 = !b2 && a.cellStyle(v2, r, c).hidden;
              if (!b2 && !h2) break;
              span++;
              c--;
            }
            const sp = document.createElement('td');
            sp.colSpan = span;
            tr.appendChild(sp);
          } else {
            const td = this._makeTD(v, a, r, c);
            td.dataset.row = r;
            td.dataset.col = c;
            cellMap.set(`${r},${c}`, td);
            tr.appendChild(td);
            c--;
          }
        }
        // Row value (1 col, adjacent to data)
        const val = document.createElement('td');
        if (showValues) { val.textContent = a.readRow(r); val.className = 'row-value'; }
        tr.appendChild(val);
        // Right spacer
        if (first > 0) {
          const sp = document.createElement('td');
          sp.colSpan = first;
          tr.appendChild(sp);
        }
      }
      tbl.appendChild(tr);
    }

    this._attachGridHover(tbl, cellMap, a);
    this._attachTooltip(tbl, '[data-row]', el => {
      const r = parseInt(el.dataset.row);
      return this._tooltipText(r, showRowLabels, showValues ? a.readRow(r) : null);
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

  _renderHexGrid({ cellSize = 24, showRowLabels = true, showValues = false, trimBlanks = true } = {}) {
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

    this._attachHexHover(svg, polyMap, a, NS);
    this._attachTooltip(svg, 'polygon[data-row]', el => {
      const r = parseInt(el.dataset.row);
      return this._tooltipText(r, showRowLabels, showValues ? a.readRow(r) : null);
    });

    this.container.innerHTML = '';
    this.container.appendChild(svg);
  }

  // ── Rotated hex grid ────────────────────────────────────────────
  // Columns slide one cell up relative to left neighbor; flat-top hexagons;
  // rows offset half a cell right.

  _renderHexGridRotated({ cellSize = 24, showRowLabels = true, showValues = false, trimBlanks = true } = {}) {
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

    this._attachHexHover(svg, polyMap, a, NS);
    this._attachTooltip(svg, 'polygon[data-row]', el => {
      const r = parseInt(el.dataset.row);
      return this._tooltipText(r, showRowLabels, showValues ? a.readRow(r) : null);
    });

    this.container.innerHTML = '';
    this.container.appendChild(svg);
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
