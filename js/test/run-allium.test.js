'use strict';

const assert = require('node:assert/strict');
const { runCheck } = require('../src/run-allium');

const CLEAN_SPEC = [
  '-- allium: 1',
  '',
  'entity Widget {',
  '    id: Integer',
  '    status: idle | active',
  '}',
  '',
  'rule Activate {',
  '    when: w: Widget.status',
  '    requires: w.status = idle',
  '    ensures: w.status = active',
  '}'
].join('\n');

const BROKEN_SPEC = ['entity Order {', '    id: UUID', '}'].join('\n');

function test(name, fn) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (exc) {
    console.error(`not ok - ${name}`);
    console.error(exc);
    process.exitCode = 1;
  }
}

test('a spec with only info/warning diagnostics has no error() and no tool error', () => {
  const result = runCheck(CLEAN_SPEC);
  assert.equal(result.error, null);
  assert.ok(Array.isArray(result.diagnostics));
  assert.ok(result.diagnostics.every((d) => d.severity !== 'error'));
});

test('a spec with an undeclared type reference reports an error diagnostic', () => {
  const result = runCheck(BROKEN_SPEC);
  assert.equal(result.error, null);
  const codes = result.diagnostics.map((d) => d.code);
  assert.ok(codes.includes('allium.type.undefinedReference'));
  const errorDiag = result.diagnostics.find((d) => d.severity === 'error');
  assert.ok(errorDiag);
  assert.equal(typeof errorDiag.line, 'number');
  assert.equal(typeof errorDiag.col, 'number');
});

test('a missing allium binary produces a not_installed tool error, not a throw', () => {
  const prev = process.env.ALLIUM_BIN;
  process.env.ALLIUM_BIN = '/no/such/allium-binary';
  try {
    const result = runCheck(CLEAN_SPEC);
    assert.equal(result.diagnostics.length, 0);
    assert.ok(result.error);
    assert.equal(result.error.kind, 'not_installed');
    assert.ok(result.error.hint.includes('brew install'));
  } finally {
    if (prev === undefined) delete process.env.ALLIUM_BIN;
    else process.env.ALLIUM_BIN = prev;
  }
});

test('runCheck never mutates process.env.ALLIUM_BIN as a side effect', () => {
  const before = process.env.ALLIUM_BIN;
  runCheck(CLEAN_SPEC);
  assert.equal(process.env.ALLIUM_BIN, before);
});

if (process.exitCode) {
  console.error('\nsome run-allium tests failed');
} else {
  console.log('\nall run-allium tests passed');
}
