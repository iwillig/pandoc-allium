"""Thin, defensive wrapper around the `allium check` CLI.

`allium check <path>...` (see `allium check --help`) validates one or more
`.allium` files and writes a JSON report of the form::

    {"command": "check", "spec_file": "...", "diagnostics": [...], "findings": [...]}

to stdout, with one entry per structural warning/error. It exits 0 when
there are no diagnostics, 1 when there is at least one diagnostic, and 2
when no `.allium` files could be resolved at all. Filesystem-level errors
(missing file, permission denied, ...) are printed as plain text to stderr
instead of JSON.

Everything that can go wrong when shelling out (binary missing, spec too
large and timing out, a future allium release changing its output shape)
is captured here as a `ToolError` rather than raised, so the pandoc filter
can always keep the document building and just report what happened.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DEFAULT_TIMEOUT = 15.0
INSTALL_HINT = "brew install juxt/allium/allium   (or: cargo install allium-cli)"
KNOWN_SEVERITIES = ("error", "warning", "info")


@dataclass
class Diagnostic:
    severity: str
    message: str
    line: Optional[int] = None
    col: Optional[int] = None
    code: Optional[str] = None

    @classmethod
    def from_json(cls, raw: dict) -> "Diagnostic":
        location = raw.get("location") or {}
        severity = raw.get("severity") or "error"
        return cls(
            severity=severity if severity in KNOWN_SEVERITIES else "error",
            message=str(raw.get("message", "")).strip(),
            line=location.get("line"),
            col=location.get("col"),
            code=raw.get("code"),
        )


@dataclass
class ToolError:
    """A reason `allium check` produced no usable diagnostics at all."""

    kind: str  # "not_installed" | "timeout" | "invalid_output" | "runtime_error"
    detail: str
    hint: Optional[str] = None


@dataclass
class CheckResult:
    diagnostics: list = field(default_factory=list)
    error: Optional[ToolError] = None

    @property
    def ran(self) -> bool:
        return self.error is None

    @property
    def has_errors(self) -> bool:
        return any(d.severity == "error" for d in self.diagnostics)

    @property
    def has_warnings(self) -> bool:
        return any(d.severity == "warning" for d in self.diagnostics)


def find_allium_binary() -> Optional[str]:
    """Resolve the allium executable, allowing an override for testing/CI."""
    return os.environ.get("ALLIUM_BIN") or shutil.which("allium")


def _not_installed() -> CheckResult:
    return CheckResult(
        error=ToolError(
            kind="not_installed",
            detail="`allium` executable not found on PATH.",
            hint=INSTALL_HINT,
        )
    )


def run_check(source: str, timeout: float = DEFAULT_TIMEOUT) -> CheckResult:
    """Run `allium check` against `source` (the verbatim code block text).

    The source is written to a private temp file untouched, so diagnostic
    line/column numbers line up exactly with the lines inside the fenced
    code block.
    """
    binary = find_allium_binary()
    if binary is None:
        return _not_installed()

    with tempfile.TemporaryDirectory(prefix="pandoc-allium-") as tmpdir:
        spec_path = Path(tmpdir) / "block.allium"
        spec_path.write_text(source, encoding="utf-8")

        try:
            proc = subprocess.run(
                [binary, "check", str(spec_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            return _not_installed()
        except subprocess.TimeoutExpired:
            return CheckResult(
                error=ToolError(
                    kind="timeout",
                    detail=f"`allium check` did not finish within {timeout:.0f}s.",
                )
            )
        except OSError as exc:
            return CheckResult(
                error=ToolError(kind="runtime_error", detail=f"Could not run `allium check`: {exc}")
            )

        stdout = proc.stdout.strip()
        if not stdout:
            detail = proc.stderr.strip() or (
                f"`allium check` exited with status {proc.returncode} and produced no output."
            )
            return CheckResult(error=ToolError(kind="runtime_error", detail=detail))

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            return CheckResult(
                error=ToolError(
                    kind="invalid_output",
                    detail=f"Could not parse `allium check` output as JSON ({exc}).",
                )
            )

        raw_diagnostics = payload.get("diagnostics")
        if not isinstance(raw_diagnostics, list):
            return CheckResult(
                error=ToolError(
                    kind="invalid_output",
                    detail="`allium check` output was valid JSON but had no `diagnostics` array.",
                )
            )

        diagnostics = [Diagnostic.from_json(d) for d in raw_diagnostics if isinstance(d, dict)]
        return CheckResult(diagnostics=diagnostics)
