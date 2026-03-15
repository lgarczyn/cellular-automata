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
    defaults: { input: 42 },
    showValues: true,
    cellSize:   32,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 0, max: 65535 },
    ],
  },
  {
    id:       'mul3plus1',
    factory:  () => new CA.MulBy3Plus1(),
    defaults: { input: 1 },
    showValues: true,
    cellSize:   32,
    controls: [
      { label: 'Number', key: 'input', type: 'number', min: 0, max: 65535 },
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
      inp.value = sec.defaults[ctrl.key] ?? '';
      if (ctrl.min !== undefined) inp.min = ctrl.min;
      if (ctrl.max !== undefined) inp.max = ctrl.max;
      controls.appendChild(inp);
      inputs[ctrl.key] = inp;
    }

    const btn = document.createElement('button');
    btn.textContent = 'Run';
    controls.appendChild(btn);
    section.appendChild(controls);

    const gridWrap = document.createElement('div');
    gridWrap.className = 'grid-wrap';
    section.appendChild(gridWrap);
    main.appendChild(section);

    const runSection = () => {
      const params = Object.fromEntries(
        Object.entries(inputs).map(([key, inp]) => {
          const v = parseInt(inp.value);
          return [key, Number.isNaN(v) ? sec.defaults[key] : v];
        })
      );
      const a    = sec.factory();
      const size = a.suggestSize(params.input ?? sec.defaults.input);
      a.run(
        params.input  ?? sec.defaults.input,
        params.width  ?? size.width,
        params.height ?? size.height,
      );
      new CA.Renderer(gridWrap, a).render({
        cellSize:      sec.cellSize,
        showRowLabels: true,
        showValues:    sec.showValues,
        trimBlanks:    true,
      });
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
