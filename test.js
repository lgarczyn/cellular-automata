"use strict";

// Minimal DOM shim so CA modules can load in Node
global.window = global;
global.document = { addEventListener() {} };

// Load CA modules in order
require('./ca-base.js');
require('./ca-rule110.js');
require('./ca-div2.js');
require('./ca-mul3.js');
require('./ca-mul3plus1.js');
require('./ca-collatz-step.js');
require('./ca-collatz-hex.js');
require('./ca-collatz-hex-rotated.js');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) {
    passed++;
  } else {
    failed++;
    console.error(`  FAIL: ${msg}`);
  }
}

function section(name) {
  console.log(`\n── ${name} ──`);
}

// ── Division by 2 ──────────────────────────────────────────────

section('Division by 2');
const RANGE = [];
for (let i = 0; i <= 1024; i++) RANGE.push(i);
for (const n of [2047, 4095, 8191, 16383, 32767, 65535, 989345275647]) RANGE.push(n);

for (const input of RANGE) {
  const a = new CA.DivBy2();
  const size = a.suggestSize(input);
  a.run(input, size.width, size.height);
  let n = input;
  let ok = true;
  for (let r = 0; r < a.height; r++) {
    const got = a.readRow(r);
    if (got !== n) {
      console.error(`  FAIL: div2(${input}) row ${r}: expected ${n}, got ${got}`);
      ok = false;
      failed++;
      break;
    }
    n = Math.floor(n / 2);
  }
  if (ok) {
    passed++;

  }
}

// ── Multiply by 3 ──────────────────────────────────────────────

section('Multiply by 3');
for (const input of RANGE) {
  const a = new CA.MulBy3();
  const height = 8;
  const size = a.suggestSize(input, height);
  a.run(input, size.width, size.height);
  let n = input;
  let ok = true;
  for (let r = 0; r < a.height; r++) {
    const got = a.readRow(r);
    if (got !== n) {
      console.error(`  FAIL: mul3(${input}) row ${r}: expected ${n}, got ${got}`);
      ok = false;
      failed++;
      break;
    }
    n *= 3;
  }
  if (ok) {
    passed++;

  }
}

// ── 3x + 1 ─────────────────────────────────────────────────────

section('3x + 1');
for (const input of RANGE) {
  const a = new CA.MulBy3Plus1();
  const height = 8;
  const size = a.suggestSize(input, height);
  a.run(input, size.width, size.height);
  let n = input;
  let ok = true;
  for (let r = 0; r < a.height; r++) {
    const got = a.readRow(r);
    if (got !== n) {
      console.error(`  FAIL: 3x+1(${input}) row ${r}: expected ${n}, got ${got}`);
      ok = false;
      failed++;
      break;
    }
    n = n * 3 + 1;
  }
  if (ok) {
    passed++;

  }
}

// ── Collatz step (3x+1 / 2) ───────────────────────────────────

section('Collatz step (3x+1 / 2)');
for (const input of RANGE.filter(n => n >= 1 && n % 2 === 1)) {
  const a = new CA.CollatzStep();
  const size = a.suggestSize(input);
  a.run(input, size.width, size.height);

  // Verify each CA row value is reachable from the previous via Collatz steps
  // (3x+1 then strip all factors of 2). Row 0 is just the input.
  const caValues = [];
  for (let r = 0; r < a.height; r++) caValues.push(a.readRow(r));

  // readRow(0) may return even value for even inputs (trailing zeros not stripped).
  // The CA internally sees the odd part. From row 1 onward, values should be odd and correct.
  // Verify the sequence from row 1 onward matches odd-only Collatz starting from oddPart(input).
  let n = input;
  while (n > 1 && n % 2 === 0) n = n / 2;
  // n is now the odd part; compute expected sequence
  const expected = [];
  while (n > 1 && expected.length < 1000) {
    n = n * 3 + 1;
    while (n > 1 && n % 2 === 0) n = n / 2;
    expected.push(n);
  }

  let ok = true;
  // Compare from row 1 onward
  for (let i = 0; i < expected.length && i + 1 < caValues.length; i++) {
    if (expected[i] !== caValues[i + 1]) {
      console.error(`  FAIL: collatz(${input}) row ${i + 1}: expected ${expected[i]}, got ${caValues[i + 1]}`);
      ok = false;
      failed++;
      break;
    }
  }
  if (ok && caValues.length - 1 < expected.length) {
    console.error(`  FAIL: collatz(${input}): CA produced ${caValues.length - 1} steps, expected ${expected.length}`);
    ok = false;
    failed++;
  }
  if (ok) {
    passed++;

  }
}

// ── Collatz hex (should match CollatzStep values) ──────────────

section('Collatz hex variants');
for (const Cls of [CA.CollatzHex, CA.CollatzHexRotated]) {
  const name = Cls === CA.CollatzHex ? 'CollatzHex' : 'CollatzHexRotated';
  for (const input of [3, 7, 27]) {
    const a = new Cls();
    const size = a.suggestSize(input);
    a.run(input, size.width, size.height);

    const ref = new CA.CollatzStep();
    const refSize = ref.suggestSize(input);
    ref.run(input, refSize.width, refSize.height);

    let ok = true;
    const len = Math.min(a.height, ref.height);
    for (let r = 0; r < len; r++) {
      const got = a.readRow(r);
      const exp = ref.readRow(r);
      if (got !== exp) {
        console.error(`  FAIL: ${name}(${input}) row ${r}: expected ${exp}, got ${got}`);
        ok = false;
        failed++;
        break;
      }
    }
    if (ok) {
      passed++;
  
    }
  }
}

// ── Summary ────────────────────────────────────────────────────

console.log(`\n${'═'.repeat(40)}`);
console.log(`  ${passed} passed, ${failed} failed`);
console.log('═'.repeat(40));
process.exit(failed > 0 ? 1 : 0);
