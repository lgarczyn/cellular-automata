"use strict";

CA.SECTIONS = [
  {
    id:       'rule110',
    factory:  () => new CA.Rule110(),
    defaults: { input: 1, width: 80, height: 60 },
    showValues: false,
    cellSize:   10,
    controls: [
      { label: 'Width', key: 'width',  type: 'number', min: 10, max: 300 },
      { label: 'Rows',  key: 'height', type: 'number', min: 5,  max: 200 },
    ],
  },
  {
    id:       'div2',
    factory:  () => new CA.DivBy2(),
    defaults: { input: 218 },
    showValues: true,
    cellSize:   32,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 0, max: 1048575 },
    ],
  },
  {
    id:       'mul3',
    factory:  () => new CA.MulBy3(),
    defaults: { input: 42, height: 10 },
    showValues: true,
    cellSize:   32,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 0, max: 65535 },
      { label: 'Rows',   key: 'height', type: 'number', min: 1, max: 200 },
    ],
  },
  {
    id:       'mul3plus1',
    factory:  () => new CA.MulBy3Plus1(),
    defaults: { input: 1, height: 10 },
    showValues: true,
    cellSize:   32,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 0, max: 65535 },
      { label: 'Rows',   key: 'height', type: 'number', min: 1, max: 200 },
    ],
  },
  {
    id:       'collatz-step',
    factory:  () => new CA.CollatzStep(),
    defaults: { input: 7 },
    showValues: true,
    cellSize:   32,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 0, max: 65535 },
    ],
    postRender(a, container) {
      // The CA does: row 0 = input, then strips factors of 2 from the
      // input before applying 3x+1. Each subsequent row is 3x+1 then strip 2s.
      const input = a.readRow(0);
      const expected = [input];
      let n = input;
      while (n > 1 && n % 2 === 0) n = n / 2;  // odd part of input
      while (n > 1 && expected.length < 1000) {
        n = n * 3 + 1;
        while (n > 1 && n % 2 === 0) n = n / 2;
        expected.push(n);
      }

      // Build comparison table
      let old = container.querySelector('.collatz-compare');
      if (old) old.remove();
      const div = document.createElement('div');
      div.className = 'collatz-compare';
      div.style.cssText = 'margin-top:1rem; font-family:"SF Mono","Cascadia Code","Consolas",monospace; font-size:0.8rem;';

      const tbl = document.createElement('table');
      tbl.style.cssText = 'border-collapse:collapse; width:auto;';
      const hdr = document.createElement('tr');
      for (const h of ['Row', 'Expected', 'CA Result', '']) {
        const th = document.createElement('th');
        th.textContent = h;
        th.style.cssText = 'padding:4px 12px; text-align:right; color:#8b949e; border-bottom:1px solid #30363d;';
        hdr.appendChild(th);
      }
      tbl.appendChild(hdr);

      const style = 'padding:3px 12px; text-align:right; border-bottom:1px solid #21262d;';
      const len = Math.min(expected.length, a.height);
      for (let r = 0; r < len; r++) {
        const exp = expected[r];
        const got = a.readRow(r);
        const match = exp === got;

        const tr = document.createElement('tr');
        for (const text of [r, exp, got]) {
          const td = document.createElement('td');
          td.textContent = text;
          td.style.cssText = style;
          tr.appendChild(td);
        }
        const tdMatch = document.createElement('td');
        tdMatch.textContent = match ? '✓' : '✗';
        tdMatch.style.cssText = style + (match ? ' color:#3fb950;' : ' color:#f85149;');
        tr.appendChild(tdMatch);
        tbl.appendChild(tr);
      }

      div.appendChild(tbl);
      container.appendChild(div);
    },
  },
  {
    id:       'collatz-hex',
    factory:  () => new CA.CollatzHex(),
    defaults: { input: 7 },
    showValues: true,
    cellSize:   28,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 1, max: 65535 },
    ],
  },
  {
    id:       'collatz-hex-rotated',
    factory:  () => new CA.CollatzHexRotated(),
    defaults: { input: 27 },
    showValues: true,
    cellSize:   28,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 1, max: 65535 },
    ],
  },
];

document.addEventListener('DOMContentLoaded', () => {
  const main = document.getElementById('main');

  for (const sec of CA.SECTIONS) {
    const automaton = sec.factory();
    const section   = document.createElement('section');
    section.id        = sec.id;
    section.className = 'ca-section';

    const h2 = document.createElement('h2');
    h2.textContent = automaton.name;
    section.appendChild(h2);

    const desc = document.createElement('p');
    desc.className  = 'desc';
    desc.textContent = automaton.description;
    section.appendChild(desc);

    // Controls
    const controls = document.createElement('div');
    controls.className = 'controls';
    const inputs = {};

    for (const ctrl of sec.controls) {
      const label = document.createElement('label');
      label.textContent = ctrl.label + ':';
      controls.appendChild(label);

      const inp = document.createElement('input');
      inp.type  = ctrl.type || 'number';
      const storageKey = `ca_${sec.id}_${ctrl.key}`;
      inp.value = localStorage.getItem(storageKey) ?? sec.defaults[ctrl.key] ?? '';
      if (ctrl.min !== undefined) inp.min = ctrl.min;
      if (ctrl.max !== undefined) inp.max = ctrl.max;
      inp.addEventListener('change', () => localStorage.setItem(storageKey, inp.value));
      controls.appendChild(inp);
      inputs[ctrl.key] = inp;
    }

    const btn = document.createElement('button');
    btn.textContent = 'Run';
    controls.appendChild(btn);
    const rowCountEl = document.createElement('span');
    rowCountEl.className = 'row-count';
    controls.appendChild(rowCountEl);
    section.appendChild(controls);

    // gridWrap is the fixed-size viewport — overflow hidden, no scrollbars
    const gridWrap = document.createElement('div');
    gridWrap.className = 'grid-wrap';

    // zoomContent holds the rendered content, positioned via translate + scale
    const zoomContent = document.createElement('div');
    zoomContent.style.transformOrigin = '0 0';
    zoomContent.style.willChange = 'transform';
    gridWrap.appendChild(zoomContent);

    // Zoom slider
    const zoomSlider = document.createElement('input');
    zoomSlider.type = 'range';
    zoomSlider.min = '5';
    zoomSlider.max = '100';
    zoomSlider.value = '100';
    zoomSlider.className = 'zoom-slider';
    zoomSlider.disabled = true;

    const zoomWrap = document.createElement('div');
    zoomWrap.style.position = 'relative';
    zoomWrap.appendChild(gridWrap);
    zoomWrap.appendChild(zoomSlider);
    section.appendChild(zoomWrap);
    main.appendChild(section);

    let zoom = 1;
    let panX = 0, panY = 0;       // content-space offset (pixels at scale=1)
    let naturalW = 0, naturalH = 0;

    const applyTransform = () => {
      zoomContent.style.transform = `translate(${panX}px,${panY}px) scale(${zoom})`;
      zoomSlider.value = String(Math.round(zoom * 100));
      zoomContent.classList.toggle('zoom-far', zoom < 0.4);
    };

    const measureContent = () => {
      const el = zoomContent.firstElementChild;
      if (!el) return;
      zoomContent.style.transform = 'none';
      naturalW = el.scrollWidth || el.offsetWidth;
      naturalH = el.scrollHeight || el.offsetHeight;
    };

    // ── Wheel zoom (around cursor) ──
    let pendingZoom = null;
    gridWrap.addEventListener('wheel', e => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
      const rect = gridWrap.getBoundingClientRect();
      // Mouse position in content-space
      const mx = (e.clientX - rect.left - panX) / zoom;
      const my = (e.clientY - rect.top  - panY) / zoom;
      const newZoom = Math.max(0.02, zoom * factor);
      // Adjust pan so point under cursor stays fixed
      panX = (e.clientX - rect.left) - mx * newZoom;
      panY = (e.clientY - rect.top)  - my * newZoom;
      zoom = newZoom;
      zoomSlider.disabled = false;
      if (!pendingZoom) {
        pendingZoom = requestAnimationFrame(() => {
          pendingZoom = null;
          applyTransform();
        });
      }
    }, { passive: false });

    // ── Drag to pan (mouse / pen only — touch is handled below) ──
    // Pointer capture is deferred until movement crosses a threshold, so a
    // stationary press-release still fires `click` on the underlying target
    // (e.g. a row-0 toggle cell). Without the threshold, setPointerCapture
    // redirects click events to gridWrap and they never reach the cells.
    let dragging = false, dragStartX = 0, dragStartY = 0, panStartX = 0, panStartY = 0;
    let pendingPointerId = null;
    const DRAG_THRESHOLD = 4;
    gridWrap.addEventListener('pointerdown', e => {
      if (e.pointerType === 'touch') return;
      if (e.button !== 0) return;
      pendingPointerId = e.pointerId;
      dragStartX = e.clientX; dragStartY = e.clientY;
      panStartX = panX; panStartY = panY;
    });
    gridWrap.addEventListener('pointermove', e => {
      if (pendingPointerId !== null && !dragging) {
        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        if (Math.hypot(dx, dy) >= DRAG_THRESHOLD) {
          dragging = true;
          gridWrap.setPointerCapture(pendingPointerId);
          gridWrap.style.cursor = 'grabbing';
        }
      }
      if (!dragging) return;
      panX = panStartX + (e.clientX - dragStartX);
      panY = panStartY + (e.clientY - dragStartY);
      applyTransform();
    });
    const stopDrag = () => { dragging = false; pendingPointerId = null; gridWrap.style.cursor = ''; };
    gridWrap.addEventListener('pointerup', stopDrag);
    gridWrap.addEventListener('pointercancel', stopDrag);

    // ── Touch: single-finger passes through to page scroll (via
    // touch-action: pan-y in CSS). Two fingers = pinch-zoom + pan. ──
    let touchGesture = null;
    gridWrap.addEventListener('touchstart', e => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const t1 = e.touches[0], t2 = e.touches[1];
        touchGesture = {
          cx: (t1.clientX + t2.clientX) / 2,
          cy: (t1.clientY + t2.clientY) / 2,
          dist: Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY),
        };
      } else {
        touchGesture = null;
      }
    }, { passive: false });
    gridWrap.addEventListener('touchmove', e => {
      if (e.touches.length !== 2 || !touchGesture) return;
      e.preventDefault();
      const t1 = e.touches[0], t2 = e.touches[1];
      const newCx = (t1.clientX + t2.clientX) / 2;
      const newCy = (t1.clientY + t2.clientY) / 2;
      const newDist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY) || touchGesture.dist;
      const rect = gridWrap.getBoundingClientRect();
      // Zoom around previous midpoint
      const scale = newDist / touchGesture.dist;
      const mx = (touchGesture.cx - rect.left - panX) / zoom;
      const my = (touchGesture.cy - rect.top  - panY) / zoom;
      const newZoom = Math.max(0.02, zoom * scale);
      panX = (touchGesture.cx - rect.left) - mx * newZoom;
      panY = (touchGesture.cy - rect.top)  - my * newZoom;
      // Plus translation from midpoint movement (two-finger pan)
      panX += newCx - touchGesture.cx;
      panY += newCy - touchGesture.cy;
      zoom = newZoom;
      touchGesture.cx = newCx;
      touchGesture.cy = newCy;
      touchGesture.dist = newDist;
      zoomSlider.disabled = false;
      applyTransform();
    }, { passive: false });
    const endTouch = e => { if (e.touches.length < 2) touchGesture = null; };
    gridWrap.addEventListener('touchend', endTouch);
    gridWrap.addEventListener('touchcancel', endTouch);

    zoomSlider.addEventListener('input', () => {
      const rect = gridWrap.getBoundingClientRect();
      const cx = rect.width / 2, cy = rect.height / 2;
      const mx = (cx - panX) / zoom;
      const my = (cy - panY) / zoom;
      zoom = parseInt(zoomSlider.value) / 100;
      panX = cx - mx * zoom;
      panY = cy - my * zoom;
      applyTransform();
    });

    const runSection = ({ preserveCamera = false } = {}) => {
      const params = Object.fromEntries(
        Object.entries(inputs).map(([key, inp]) => {
          const v = parseInt(inp.value);
          return [key, Number.isNaN(v) ? sec.defaults[key] : v];
        })
      );
      const a    = sec.factory();
      const input  = params.input  ?? sec.defaults.input;
      const size   = a.suggestSize(input, params.height);
      const height = params.height ?? size.height;
      const width  = params.width  ?? size.width;
      a.run(input, width, height);
      new CA.Renderer(zoomContent, a).render({
        cellSize:      sec.cellSize,
        showRowLabels: true,
        showValues:    sec.showValues,
        trimBlanks:    true,
        // Toggle row-0 bits by clicking. Updates the input field + re-runs
        // without resetting the user's pan/zoom.
        onCellClick: 'input' in inputs ? (r, c) => {
          if (r !== 0) return;
          const bitIdx = a.bitColToIndex(c);
          if (bitIdx === null || bitIdx < 0) return;
          const mask = Math.pow(2, bitIdx);
          const isSet = Math.floor(input / mask) % 2 === 1;
          const newN = isSet ? input - mask : input + mask;
          if (newN < (inputs.input.min !== '' ? parseInt(inputs.input.min) : 0)) return;
          inputs.input.value = newN;
          localStorage.setItem(`ca_${sec.id}_input`, String(newN));
          runSection({ preserveCamera: true });
        } : null,
      });
      // Show row count next to the Run button.
      rowCountEl.textContent = `${a.height} ${a.height === 1 ? 'row' : 'rows'}`;
      if (!preserveCamera) {
        // Auto-zoom to fit viewport on a fresh Run / first render.
        measureContent();
        const vw = gridWrap.clientWidth;
        const vh = gridWrap.clientHeight;
        const fitW = naturalW > 0 ? vw / naturalW : 1;
        const fitH = naturalH > 0 ? vh / naturalH : 1;
        zoom = Math.min(1, fitW, fitH);
        panX = 0; panY = 0;
        applyTransform();
        zoomSlider.disabled = zoom >= 1;
      }
      // On preserveCamera, leave zoomContent.style.transform untouched —
      // it persists across innerHTML replacements, so the user's pan/zoom
      // stays exactly where it was. We deliberately skip measureContent()
      // because it transiently sets transform:'none' (causing the wiggle).
      if (sec.postRender) sec.postRender(a, section);
    };

    btn.addEventListener('click', () => runSection());
    runSection();
  }

  CA.HailstoneRecords.render(main);

  // Highlight active nav link based on scroll position
  const sections = document.querySelectorAll('section.ca-section');
  const navLinks = document.querySelectorAll('#main-nav a');
  const observer = new IntersectionObserver(entries => {
    for (const e of entries) {
      if (e.isIntersecting)
        navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id));
    }
  }, { rootMargin: '-40% 0px -50% 0px' });
  sections.forEach(s => observer.observe(s));
});
