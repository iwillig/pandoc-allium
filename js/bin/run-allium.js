#!/usr/bin/env node
'use strict';

/**
 * Standalone CLI wrapper: `run-allium file1.allium [file2.allium ...]`
 *
 * Thin terminal front-end for src/run-allium.js, useful for checking specs
 * from a JS/Node toolchain (npm scripts, a docs build, CI) without needing
 * the pandoc filter in the loop at all.
 *
 * Exit codes mirror `allium check` itself:
 *   0  every file checked clean
 *   1  at least one file had a diagnostic (error/warning/info)
 *   2  no input files given, or allium itself could not be run
 */

const fs = require('node:fs');
const path = require('node:path');
const { runCheck } = require('../src/run-allium');

function printReport(file, result) {
  if (result.error) {
    console.error(`${file}: allium check could not run -- ${result.error.detail}`);
    if (result.error.hint) {
      console.error(`  fix: ${result.error.hint}`);
    }
    return 'tool_error';
  }

  if (result.diagnostics.length === 0) {
    console.log(`${file}: ok`);
    return 'clean';
  }

  let worst = 'info';
  for (const d of result.diagnostics) {
    const loc = d.line != null ? `${d.line}:${d.col != null ? d.col : '?'}` : '-';
    console.log(`${file}:${loc}: [${d.severity}] ${d.message}${d.code ? ` (${d.code})` : ''}`);
    if (d.severity === 'error') worst = 'error';
    else if (d.severity === 'warning' && worst !== 'error') worst = 'warning';
  }
  return worst;
}

function main(argv) {
  const files = argv.slice(2);
  if (files.length === 0) {
    console.error('usage: run-allium <file.allium> [file2.allium ...]');
    return 2;
  }

  let sawToolError = false;
  let sawDiagnostic = false;

  for (const file of files) {
    let source;
    try {
      source = fs.readFileSync(path.resolve(file), 'utf8');
    } catch (exc) {
      console.error(`${file}: ${exc.message}`);
      sawToolError = true;
      continue;
    }

    const result = runCheck(source);
    const outcome = printReport(file, result);
    if (outcome === 'tool_error') sawToolError = true;
    else if (outcome === 'error' || outcome === 'warning') sawDiagnostic = true;
  }

  if (sawToolError) return 2;
  if (sawDiagnostic) return 1;
  return 0;
}

process.exit(main(process.argv));
