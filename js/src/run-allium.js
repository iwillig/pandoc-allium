'use strict';

/**
 * Node.js counterpart to pandoc_allium/allium_cli.py: a small, dependency-free
 * wrapper around the `allium check` CLI (https://juxt.github.io/allium/).
 *
 * `allium check <path>...` writes a JSON report to stdout of the form
 * `{command, spec_file, diagnostics: [...], findings: [...]}` and exits 0
 * (clean), 1 (one or more diagnostics), or 2 (no .allium files resolved).
 * Filesystem-level errors (missing file, ...) go to stderr as plain text
 * instead of JSON. Everything that can go wrong invoking the binary --
 * missing install, a spec that hangs the checker, a future release
 * changing its output shape -- is captured as a `{kind, detail, hint}`
 * tool error instead of thrown, so callers can always decide how to
 * degrade instead of crashing.
 */

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const DEFAULT_TIMEOUT_MS = 15000;
const INSTALL_HINT = 'brew install juxt/allium/allium   (or: cargo install allium-cli)';
const KNOWN_SEVERITIES = new Set(['error', 'warning', 'info']);

function findAlliumBinary() {
  return process.env.ALLIUM_BIN || 'allium';
}

function toDiagnostic(raw) {
  const location = raw.location || {};
  const severity = KNOWN_SEVERITIES.has(raw.severity) ? raw.severity : 'error';
  return {
    severity,
    message: String(raw.message || '').trim(),
    line: typeof location.line === 'number' ? location.line : null,
    col: typeof location.col === 'number' ? location.col : null,
    code: raw.code != null ? raw.code : null
  };
}

function notInstalled() {
  return {
    diagnostics: [],
    error: {
      kind: 'not_installed',
      detail: '`allium` executable not found on PATH.',
      hint: INSTALL_HINT
    }
  };
}

/**
 * Run `allium check` against `source` (the verbatim spec text).
 *
 * @param {string} source
 * @param {{timeoutMs?: number}} [options]
 * @returns {{diagnostics: Array<object>, error: ?{kind: string, detail: string, hint?: string}}}
 */
function runCheck(source, options = {}) {
  const timeoutMs = options.timeoutMs || DEFAULT_TIMEOUT_MS;
  const binary = findAlliumBinary();

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pandoc-allium-'));
  const specPath = path.join(tmpDir, 'block.allium');

  try {
    fs.writeFileSync(specPath, source, 'utf8');

    const result = spawnSync(binary, ['check', specPath], {
      encoding: 'utf8',
      timeout: timeoutMs
    });

    if (result.error) {
      if (result.error.code === 'ENOENT') {
        return notInstalled();
      }
      if (result.error.code === 'ETIMEDOUT') {
        return {
          diagnostics: [],
          error: {
            kind: 'timeout',
            detail: `\`allium check\` did not finish within ${Math.round(timeoutMs / 1000)}s.`
          }
        };
      }
      return {
        diagnostics: [],
        error: { kind: 'runtime_error', detail: `Could not run \`allium check\`: ${result.error.message}` }
      };
    }

    const stdout = (result.stdout || '').trim();
    if (!stdout) {
      const detail =
        (result.stderr || '').trim() ||
        `\`allium check\` exited with status ${result.status} and produced no output.`;
      return { diagnostics: [], error: { kind: 'runtime_error', detail } };
    }

    let payload;
    try {
      payload = JSON.parse(stdout);
    } catch (exc) {
      return {
        diagnostics: [],
        error: { kind: 'invalid_output', detail: `Could not parse \`allium check\` output as JSON (${exc.message}).` }
      };
    }

    if (!Array.isArray(payload.diagnostics)) {
      return {
        diagnostics: [],
        error: { kind: 'invalid_output', detail: '`allium check` output was valid JSON but had no `diagnostics` array.' }
      };
    }

    return {
      diagnostics: payload.diagnostics.filter((d) => d && typeof d === 'object').map(toDiagnostic),
      error: null
    };
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

module.exports = { runCheck, findAlliumBinary, INSTALL_HINT };
