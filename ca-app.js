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
      // Compute full Collatz sequence (including even steps)
      const input = a.readRow(0);
      const fullSeq = [input];
      let n = input;
      while (n > 1 && fullSeq.length < 1000) {
        n = (n % 2 === 0) ? n / 2 : n * 3 + 1;
        fullSeq.push(n);
      }

      // Get CA row values (odd-only steps)
      const caValues = [];
      for (let r = 0; r < a.height; r++) caValues.push(a.readRow(r));

      // Build comparison table
      let old = container.querySelector('.collatz-compare');
      if (old) old.remove();
      const div = document.createElement('div');
      div.className = 'collatz-compare';
      div.style.cssText = 'margin-top:1rem; font-family:"SF Mono","Cascadia Code","Consolas",monospace; font-size:0.8rem;';

      const tbl = document.createElement('table');
      tbl.style.cssText = 'border-collapse:collapse; width:auto;';
      const hdr = document.createElement('tr');
      for (const h of ['Step', 'Expected', 'CA Result', '']) {
        const th = document.createElement('th');
        th.textContent = h;
        th.style.cssText = 'padding:4px 12px; text-align:right; color:#8b949e; border-bottom:1px solid #30363d;';
        hdr.appendChild(th);
      }
      tbl.appendChild(hdr);

      // Map full sequence to CA rows: odd values match CA rows, even values show empty
      let caIdx = 0;
      for (let i = 0; i < fullSeq.length; i++) {
        const exp = fullSeq[i];
        const isOdd = exp % 2 === 1 || exp === 1;
        const got = isOdd && caIdx < caValues.length ? caValues[caIdx] : null;
        const match = got !== null && exp === got;
        const style = 'padding:3px 12px; text-align:right; border-bottom:1px solid #21262d;';
        const dimStyle = style + ' color:#484f58;';

        const tr = document.createElement('tr');
        // Step
        const tdStep = document.createElement('td');
        tdStep.textContent = i;
        tdStep.style.cssText = isOdd ? style : dimStyle;
        tr.appendChild(tdStep);
        // Expected
        const tdExp = document.createElement('td');
        tdExp.textContent = exp;
        tdExp.style.cssText = isOdd ? style : dimStyle;
        tr.appendChild(tdExp);
        // CA Result
        const tdGot = document.createElement('td');
        tdGot.textContent = got !== null ? got : '';
        tdGot.style.cssText = isOdd ? style : dimStyle;
        tr.appendChild(tdGot);
        // Match indicator
        const tdMatch = document.createElement('td');
        tdMatch.textContent = isOdd ? (match ? '✓' : '✗') : '';
        tdMatch.style.cssText = style + (match ? ' color:#3fb950;' : ' color:#f85149;');
        tr.appendChild(tdMatch);
        tbl.appendChild(tr);

        if (isOdd) caIdx++;
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
    defaults: { input: 7 },
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
    section.appendChild(controls);

    // gridWrap is the fixed-size scroll viewport (never changes size)
    const gridWrap = document.createElement('div');
    gridWrap.className = 'grid-wrap';

    // zoomSizer takes up space matching the scaled content, driving scrollbars
    const zoomSizer = document.createElement('div');
    // zoomContent holds the actual rendered content, scaled via transform
    const zoomContent = document.createElement('div');
    zoomContent.style.transformOrigin = 'top left';
    zoomContent.style.willChange = 'transform';
    zoomContent.style.position = 'absolute';
    zoomContent.style.top = '0';
    zoomContent.style.left = '0';
    zoomSizer.style.position = 'relative';
    zoomSizer.appendChild(zoomContent);
    gridWrap.appendChild(zoomSizer);

    // Zoom slider — fixed in the viewport corner, not inside scrollable area
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
    let naturalW = 0, naturalH = 0;

    // Cached viewport dimensions — updated on resize/run, never in wheel handler
    let cachedVW = 0, cachedVH = 0, cachedRect = null;
    const updateCache = () => {
      cachedVW = gridWrap.clientWidth;
      cachedVH = gridWrap.clientHeight;
      cachedRect = gridWrap.getBoundingClientRect();
    };
    new ResizeObserver(updateCache).observe(gridWrap);

    // Layout-only update: resizes sizer to match zoom (triggers reflow)
    const applyLayout = () => {
      const padX = cachedVW / 2;
      const padY = cachedVH / 2;
      zoomContent.style.left = padX + 'px';
      zoomContent.style.top  = padY + 'px';
      zoomSizer.style.width  = (naturalW * zoom + padX * 2) + 'px';
      zoomSizer.style.height = (naturalH * zoom + padY * 2) + 'px';
      updateCache();
    };

    // Fast update: only transform + slider (no reflow)
    const applyTransform = () => {
      zoomContent.style.transform = `scale(${zoom})`;
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

    // Track scroll position without forcing reflow
    let cachedScrollX = 0, cachedScrollY = 0;
    gridWrap.addEventListener('scroll', () => {
      cachedScrollX = gridWrap.scrollLeft;
      cachedScrollY = gridWrap.scrollTop;
    }, { passive: true });

    let pendingZoom = null;
    let zoomAnchor = null;
    gridWrap.addEventListener('wheel', e => {
      if (!e.altKey) return;
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;

      // Use cached values — no layout reads here
      const padX = cachedVW / 2;
      const padY = cachedVH / 2;
      const mx = (e.clientX - cachedRect.left + cachedScrollX - padX) / zoom;
      const my = (e.clientY - cachedRect.top  + cachedScrollY - padY) / zoom;

      zoom = Math.min(1, Math.max(0.05, zoom * factor));
      zoomSlider.disabled = false;
      zoomAnchor = { mx, my, cx: e.clientX - cachedRect.left, cy: e.clientY - cachedRect.top, padX, padY };

      if (!pendingZoom) {
        pendingZoom = requestAnimationFrame(() => {
          pendingZoom = null;
          const a = zoomAnchor;
          // All reads first (from cache — no layout reads)
          const sx = a.mx * zoom + a.padX - a.cx;
          const sy = a.my * zoom + a.padY - a.cy;
          // All writes batched together (no reads after)
          applyTransform();
          zoomSizer.style.width  = (naturalW * zoom + a.padX * 2) + 'px';
          zoomSizer.style.height = (naturalH * zoom + a.padY * 2) + 'px';
          gridWrap.scrollTo(sx, sy);
          cachedScrollX = sx;
          cachedScrollY = sy;
        });
      }
    }, { passive: false });

    zoomSlider.addEventListener('input', () => {
      zoom = parseInt(zoomSlider.value) / 100;
      applyTransform();
      applyLayout();
    });

    const runSection = () => {
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
      });
      measureContent();
      updateCache();
      // Auto-zoom to fit if content overflows
      const fitW = naturalW > 0 ? cachedVW / naturalW : 1;
      const fitH = naturalH > 0 ? cachedVH / naturalH : 1;
      zoom = Math.min(1, fitW, fitH);
      applyTransform();
      applyLayout();
      // Scroll to top-left of actual content (past the padding)
      gridWrap.scrollLeft = cachedVW / 2;
      gridWrap.scrollTop  = cachedVH / 2;
      cachedScrollX = gridWrap.scrollLeft;
      cachedScrollY = gridWrap.scrollTop;
      zoomSlider.disabled = zoom >= 1;
      if (sec.postRender) sec.postRender(a, section);
    };

    btn.addEventListener('click', runSection);
    runSection();
  }

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
