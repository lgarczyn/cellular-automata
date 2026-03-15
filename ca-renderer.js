"use strict";

CA.Renderer = class Renderer {

  constructor(container, automaton) {
    this.container = container;
    this.automaton = automaton;
  }

  render(opts = {}) {
    const mode = this.automaton.displayMode;
    if (mode === 'hexgrid')    this._renderHexGrid(opts);
    else if (mode === 'hex')   this._renderHex(opts);
    else                       this._renderGrid(opts);
  }

  // ── Square grid (table) ──────────────────────────────────────────

  _renderGrid({ cellSize = 28, showRowLabels = true, showValues = false, trimBlanks = true } = {}) {
    const a    = this.automaton;
    const grid = trimBlanks ? a.trimmedGrid() : a.grid;
    this.container.style.setProperty('--cell-size', cellSize + 'px');

    const cellMap = new Map();
    const tbl = document.createElement('table');
    for (let r = 0; r < grid.length; r++) {
      const tr = document.createElement('tr');
      if (showRowLabels) tr.appendChild(this._labelTD(r));
      for (let c = grid[r].length - 1; c >= 0; c--) {
        const td = this._makeTD(grid[r][c], a);
        td.dataset.row = r;
        td.dataset.col = c;
        cellMap.set(`${r},${c}`, td);
        tr.appendChild(td);
      }
      if (showValues) tr.appendChild(this._valueTD(a.readRow(r)));
      tbl.appendChild(tr);
    }

    this._attachGridHover(tbl, cellMap, a);

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
      if (showRowLabels) tr.appendChild(this._labelTD(r));

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

      if (showValues) tr.appendChild(this._valueTD(a.readRow(r)));
      tbl.appendChild(tr);
    }

    this.container.innerHTML = '';
    this.container.appendChild(tbl);
  }

  // ── Flat-top hexagonal grid (SVG) ───────────────────────────────

  _renderHexGrid({ cellSize = 24, showRowLabels = true, showValues = false, trimBlanks = true } = {}) {
    const a    = this.automaton;
    const grid = trimBlanks ? a.trimmedGrid() : a.grid;

    const R       = cellSize / 2;
    const sqrt3   = Math.sqrt(3);
    const hexW    = sqrt3 * R;            // pointy-top hex width

    const numRows = grid.length;
    const numCols = grid[0]?.length ?? 0;

    const valueW = showValues ? 80 : 0;
    const padX   = hexW / 2 + 8;
    const padY   = R + (showRowLabels ? 16 : 2);

    const svgW = padX + (numRows - 1) * hexW + (numCols - 1) * hexW / 2 + hexW / 2 + valueW + 8;
    const svgH = padY + (numCols - 1) * 1.5 * R + R + 4;

    const NS  = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', svgW);
    svg.setAttribute('height', svgH);
    svg.style.display = 'block';

    // Rotate 60° CW — compute rotated bounding box for the container
    const angle = 60;
    const rad = angle * Math.PI / 180;
    const cosA = Math.abs(Math.cos(rad));
    const sinA = Math.abs(Math.sin(rad));
    const rotW = svgW * cosA + svgH * sinA;
    const rotH = svgW * sinA + svgH * cosA;
    svg.style.transform = `rotate(${angle}deg)`;
    svg.style.transformOrigin = 'center center';

    // Inject hover style for row values
    const style = document.createElementNS(NS, 'style');
    style.textContent = '.hex-row .row-val { opacity: 0; transition: opacity 0.15s; }'
                      + '.hex-row:hover .row-val { opacity: 1; }'
                      + '.hex-row:hover polygon { filter: brightness(1.2); }';
    svg.appendChild(style);

    const fontSize = Math.max(7, R * 0.7);
    const carryStroke   = '#f0883e';
    const defaultStroke = '#21262d';
    const polyMap = new Map();

    for (let r = 0; r < numRows; r++) {
      const g = document.createElementNS(NS, 'g');
      g.setAttribute('class', 'hex-row');

      // Row label at the top of the diagonal (c=0 = MSB, top of stripe)
      if (showRowLabels) {
        const lx = padX + r * hexW;
        const ly = padY - R - 3;
        const txt = document.createElementNS(NS, 'text');
        txt.setAttribute('x', lx);
        txt.setAttribute('y', ly);
        txt.setAttribute('text-anchor', 'middle');
        txt.setAttribute('fill', '#8b949e');
        txt.setAttribute('font-size', '9');
        txt.setAttribute('font-family', 'sans-serif');
        txt.textContent = r;
        g.appendChild(txt);
      }

      for (let c = 0; c < grid[r].length; c++) {
        const cx = padX + r * hexW + c * hexW / 2;
        const cy = padY + c * 1.5 * R;

        const cell  = grid[r][c];
        const cs    = a.cellStyle(cell);
        const carry = cs.carry || false;

        // Hexagon
        const poly = document.createElementNS(NS, 'polygon');
        poly.setAttribute('points', this._hexPoints(cx, cy, R));
        poly.setAttribute('fill', cs.colors[0]);
        poly.setAttribute('stroke', carry ? carryStroke : defaultStroke);
        poly.setAttribute('stroke-width', carry ? '2.5' : '1');
        poly.dataset.row = r;
        poly.dataset.col = c;
        polyMap.set(`${r},${c}`, poly);
        g.appendChild(poly);

        // Cell text
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

      // Row value (hidden until hover)
      if (showValues) {
        const n = a.readRow(r);
        if (n !== null) {
          const lastC = Math.max(0, grid[r].length - 1);
          const valX = padX + r * hexW + lastC * hexW / 2 + hexW / 2 + 10;
          const valY = padY + lastC * 1.5 * R + 4;
          const txt  = document.createElementNS(NS, 'text');
          txt.setAttribute('x', valX);
          txt.setAttribute('y', valY);
          txt.setAttribute('class', 'row-val');
          txt.setAttribute('fill', '#3fb950');
          txt.setAttribute('font-size', '11');
          txt.setAttribute('font-family', "'SF Mono','Cascadia Code','Consolas',monospace");
          txt.textContent = n;
          g.appendChild(txt);
        }
      }

      svg.appendChild(g);
    }

    this._attachHexHover(svg, polyMap, a, NS);

    this.container.innerHTML = '';
    const wrapper = document.createElement('div');
    wrapper.style.width  = rotW + 'px';
    wrapper.style.height = rotH + 'px';
    wrapper.style.display = 'flex';
    wrapper.style.alignItems = 'center';
    wrapper.style.justifyContent = 'center';
    wrapper.style.overflow = 'visible';
    wrapper.appendChild(svg);
    this.container.appendChild(wrapper);
  }

  // Flat-top hexagon vertex string for SVG polygon
  _hexPoints(cx, cy, R) {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const angle = Math.PI / 6 + Math.PI / 3 * i;  // pointy-top: start at 30°
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

  _labelTD(r) {
    const td = document.createElement('td');
    td.className = 'row-label';
    td.textContent = r;
    return td;
  }

  _valueTD(n) {
    const td = document.createElement('td');
    td.className = 'row-value';
    td.textContent = n !== null ? n : '';
    return td;
  }

  _makeTD(value, automaton) {
    const td    = document.createElement('td');
    const style = automaton.cellStyle(value);
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
    if (style.carry) td.style.boxShadow = 'inset 0 0 0 2px #f0883e';
    td.textContent = style.text;
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
