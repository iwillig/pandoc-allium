'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { Given, When, Then, Before, After } = require('@cucumber/cucumber');

const CLI_PATH = path.join(__dirname, '..', '..', 'bin', 'run-allium.js');

Before(function () {
  this.tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'run-allium-features-'));
  this.env = { ...process.env };
  this.result = null;
});

After(function () {
  fs.rmSync(this.tmpDir, { recursive: true, force: true });
});

Given('a spec file named {string} with:', function (fileName, specText) {
  fs.writeFileSync(path.join(this.tmpDir, fileName), specText, 'utf8');
});

Given('allium is not installed', function () {
  this.env.ALLIUM_BIN = '/no/such/allium-binary';
});

function runCli(world, fileNames) {
  world.result = spawnSync(process.execPath, [CLI_PATH, ...fileNames], {
    cwd: world.tmpDir,
    encoding: 'utf8',
    env: world.env
  });
}

When('I run the CLI against {string}', function (fileName) {
  runCli(this, [fileName]);
});

When('I run the CLI against {string} and {string}', function (first, second) {
  runCli(this, [first, second]);
});

When('I run the CLI with no files', function () {
  runCli(this, []);
});

Then('the CLI exits with status {int}', function (status) {
  assert.equal(this.result.status, status);
});

Then('the output reports {string}', function (line) {
  assert.ok(
    this.result.stdout.includes(line),
    `expected stdout to include ${JSON.stringify(line)}, got:\n${this.result.stdout}`
  );
});

Then('the output includes an {string} diagnostic mentioning {string}', function (severity, needle) {
  const hasMatchingLine = this.result.stdout
    .split('\n')
    .some((line) => line.includes(`[${severity}]`) && line.includes(needle));
  assert.ok(
    hasMatchingLine,
    `expected stdout to include a [${severity}] diagnostic mentioning ${JSON.stringify(needle)}, got:\n${this.result.stdout}`
  );
});

Then('stderr includes {string}', function (needle) {
  assert.ok(
    this.result.stderr.includes(needle),
    `expected stderr to include ${JSON.stringify(needle)}, got:\n${this.result.stderr}`
  );
});
