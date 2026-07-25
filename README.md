# pandoc-allium

[![CI](https://github.com/iwillig/pandoc-allium/actions/workflows/ci.yml/badge.svg)](https://github.com/iwillig/pandoc-allium/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pandoc-allium.svg)](https://pypi.org/project/pandoc-allium/)

## Install

```sh
pip install pandoc-allium
```

This registers the `pandoc-allium` console script on `PATH`. You'll also
need the `allium` CLI itself and pandoc -- see [Requirements](#requirements)
below. Then run pandoc with the filter:

```sh
pandoc -F pandoc-allium \
  --syntax-definition "$(pandoc-allium --syntax-path)" \
  -s examples/demo.md -o demo.html
```

A [pandoc](https://pandoc.org/) filter for the [Allium](https://juxt.github.io/allium/)
specification language. For every fenced code block written as:

````markdown
```allium
-- allium: 1

entity Widget {
    id: Integer
    status: idle | active
}

rule Activate {
    when: w: Widget.status
    requires: w.status = idle
    ensures: w.status = active
}
```
````

the filter runs `allium check` against exactly that text and inserts a
diagnostics report right after the block. **The original source is never
altered** -- the filter only ever adds a block after it, so re-extracting
the code (or handing the doc to another tool) always gets byte-for-byte
what you wrote.

![Diagnostics output](images/example-allium-spec.png)

Syntax highlighting is handled separately and natively by pandoc's own
[Skylighting](https://hackage.haskell.org/package/skylighting) engine via a
bundled Kate syntax definition -- no JavaScript required for that part. A
small Node package is also included for running `allium check` from a JS
toolchain (npm scripts, CI, a docs build) independent of pandoc.

## Requirements

- [pandoc](https://pandoc.org/) (tested against the Homebrew build, 3.9.x)
- the `allium` CLI itself: `brew install juxt/allium/allium` (or `cargo
  install allium-cli`) -- see <https://juxt.github.io/allium/installation>
- Python 3.9+ and [pipenv](https://pipenv.pypa.io/), for the pandoc filter
- Node 22+ (cucumber-js requires it) and [yarn](https://yarnpkg.com/), only
  if you want the JS runner ([nvm](https://github.com/nvm-sh/nvm) users:
  `cd js && nvm use` picks up the pinned version from `js/.nvmrc`)

## Local LLM development (Apple Silicon only)

The repo includes an optional local LLM setup for offline, AI-assisted
coding via the [`pi`](https://github.com/nicholasgriffintaylor/pi) agent
framework. It runs the
[unsloth/Qwen3.6-27B-MLX-8bit](https://huggingface.co/unsloth/Qwen3.6-27B-MLX-8bit)
model entirely on-device using Apple's
[MLX](https://github.com/ml-explore/mlx) framework — no API keys or
network access required.

### How it works

The `Pipfile` conditionally installs `mlx-vlm` on macOS (`sys_platform ==
'darwin'`). This gives two `just` recipes:

- **`just chat-qwen`** — starts an interactive chat session with the model
  via `mlx_vlm.chat`. Good for quick questions.
- **`just serve-qwen`** — starts an OpenAI-compatible HTTP server at
  `http://localhost:8080/v1` via `mlx_vlm.server`. Leave this running in
  its own terminal; the `pi` agent connects to it as its provider.

The `.pi/settings.json` file tells `pi` to use the `mlx-lm` provider
pointing at `unsloth/Qwen3.6-27B-MLX-8bit` as the default model.

### System prompt

`.pi/SYSTEM.md` replaces `pi`'s default system prompt with a project-
specific brief. It covers:

- **Tools** — which capabilities the agent has (`read`, `bash`, `edit`,
  `write`) and how to use them.
- **Working style** — conventions like "read before you write," "verify
  with project commands," and "never alter the original fenced block."
- **Project context** — a summary of the codebase layout, module
  responsibilities, and repo-specific conventions.
- **Commands** — the `just` recipes the agent should use for testing and
  linting.

Edit `.pi/SYSTEM.md` to change the agent's behavior for this project.

## Python filter (pipenv)

```sh
pipenv install --dev
```

This installs the package itself (editable) plus its one dependency,
[panflute](https://github.com/sergiocorreia/panflute), and registers the
`pandoc-allium` console script inside the pipenv virtualenv. Run pandoc
through `pipenv run` so that script is on `PATH` (your system's Homebrew
`pandoc` is used as-is -- pipenv never shadows it):

```sh
pipenv run pandoc -F pandoc-allium \
  --syntax-definition "$(pipenv run pandoc-allium --syntax-path)" \
  -s examples/demo.md -o demo.html
```

`--syntax-definition` is optional but recommended: without it, `allium`
code blocks still get checked, they just render as plain unhighlighted
code. It works identically for HTML, LaTeX/PDF, docx, and every other
Skylighting-backed writer pandoc has. `pandoc-allium --syntax-path` prints
the syntax file's installed, absolute path, so this works the same way
whether you installed via `pipenv`, `pip install pandoc-allium`, or an
editable checkout.

### Opting out per block

Add `.no-check` to a block's classes to keep it in a doc (e.g. to show a
deliberately-broken example) without ever invoking `allium`:

````markdown
```{.allium .no-check}
this isn't valid allium and that's the point
```
````

### Error handling

Nothing about a broken environment should take down the whole pandoc run.
`pandoc_allium/allium_cli.py` classifies everything that can go wrong into
a `ToolError` and the filter renders it as a normal diagnostics block
instead of crashing:

| situation                                   | reported as        |
|----------------------------------------------|--------------------|
| `allium` not on `PATH`                        | `not_installed` (with the install command as a fix-it hint) |
| spec takes longer than the timeout (15s default) | `timeout`       |
| non-JSON or unexpected stdout shape           | `invalid_output`   |
| any other non-zero exit / stderr-only failure | `runtime_error`    |

Set `ALLIUM_BIN=/path/to/allium` to point at a specific binary (also used
by the test suite to substitute a fake binary).

### Tests

```sh
pipenv run pytest
```

## JS runner (yarn)

`js/` is a small, dependency-free Node package that wraps `allium check`
the same way `allium_cli.py` does, for use outside of pandoc (npm scripts,
CI, a docs pipeline):

```sh
cd js
yarn install
yarn test
```

As a library:

```js
const { runCheck } = require('./js/src/run-allium');
const result = runCheck(specSourceText);
// result.error, or result.diagnostics: [{severity, message, line, col, code}, ...]
```

As a standalone CLI:

```sh
node js/bin/run-allium.js path/to/spec.allium
```

Exit codes match `allium check` itself: `0` clean, `1` one or more
diagnostics, `2` no input files or `allium` couldn't be run at all.

### Feature tests (Cucumber)

`yarn test` runs the unit suite (`test/`) and then a
[cucumber-js](https://github.com/cucumber/cucumber-js) suite (`features/`)
that drives the actual `bin/run-allium.js` CLI end-to-end -- writing real
spec files to a temp dir and asserting on exit codes and stdout/stderr --
to read as a plain-language description of what this system guarantees
(a clean spec exits 0, an invalid one is reported as an error, a missing
`allium` install fails with a helpful hint, etc). Run just that suite with:

```sh
cd js
yarn test:features
```

## Layout

```
pandoc_allium/
  allium_cli.py   subprocess wrapper around `allium check` (+ error classification)
  render.py       builds the diagnostics Div from a CheckResult
  filter.py       the panflute filter itself (entry point: pandoc-allium)
  syntax/allium.xml  Kate/Skylighting syntax definition for native highlighting
js/
  src/run-allium.js   Node port of allium_cli.py
  bin/run-allium.js   standalone CLI
  test/               unit tests for src/run-allium.js
  features/           cucumber-js feature tests driving bin/run-allium.js end-to-end
.pi/
  settings.json   pi agent config (default provider + model)
  SYSTEM.md       project-specific system prompt for the pi agent
tests/            pytest suite (fixtures/ holds raw .allium snippets)
examples/         demo.md, common-errors.md, workflow.md, multi-entity.md
```
