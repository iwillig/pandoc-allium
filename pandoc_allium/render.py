"""Turn an allium_cli.CheckResult into pandoc AST nodes.

The ```allium code block itself is never touched by this module -- the
filter leaves the original `CodeBlock` node exactly as pandoc parsed it.
Syntax highlighting is handled natively by pandoc's own Skylighting engine
via the bundled `pandoc_allium/syntax/allium.xml` Kate syntax definition
(pass `--syntax-definition pandoc_allium/syntax/allium.xml` to pandoc), so
no JavaScript or markup rewriting is needed, and it works identically
across every writer (HTML, LaTeX/PDF, docx, ...).

This module only builds the diagnostics block that follows the code block,
out of generic pandoc elements (Div/Para/BulletList) so it degrades
sensibly in any output format. Nothing is rendered when the check is clean.
"""

from __future__ import annotations

from typing import Optional

import panflute as pf

from .allium_cli import CheckResult, Diagnostic, ToolError

SEVERITY_ICON = {"error": "[error]", "warning": "[warn]", "info": "[info]"}
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def _location(diag: Diagnostic) -> str:
    if diag.line is None:
        return ""
    if diag.col is None:
        return f"line {diag.line}"
    return f"line {diag.line}:{diag.col}"


def _diagnostic_item(diag: Diagnostic) -> pf.ListItem:
    tag = SEVERITY_ICON.get(diag.severity, f"[{diag.severity}]")
    inlines = [pf.Strong(pf.Str(tag))]
    loc = _location(diag)
    if loc:
        inlines += [pf.Space, pf.Emph(pf.Str(f"({loc})"))]
    inlines += [pf.Space, pf.Str(" ".join(diag.message.split()))]
    if diag.code:
        inlines += [pf.Space, pf.Code(diag.code)]
    return pf.ListItem(pf.Para(*inlines))


def _summary_text(result: CheckResult) -> str:
    counts = {"error": 0, "warning": 0, "info": 0}
    for d in result.diagnostics:
        counts[d.severity] = counts.get(d.severity, 0) + 1
    parts = [f"{n} {sev}{'s' if n != 1 else ''}" for sev, n in counts.items() if n]
    return "allium check: " + (", ".join(parts) if parts else "no diagnostics")


def _worst_severity(result: CheckResult) -> str:
    if not result.diagnostics:
        return "info"
    return min((d.severity for d in result.diagnostics), key=lambda s: SEVERITY_ORDER.get(s, 9))


def diagnostics_block(result: CheckResult) -> Optional[pf.Div]:
    """Build the diagnostics Div, or None when there's nothing worth showing."""
    if result.error is not None:
        return _tool_error_block(result.error)

    if not result.diagnostics:
        return None

    ordered = sorted(result.diagnostics, key=lambda d: SEVERITY_ORDER.get(d.severity, 9))
    items = [_diagnostic_item(d) for d in ordered]
    summary = pf.Para(pf.Strong(pf.Str(_summary_text(result))))
    classes = ["allium-diagnostics", f"allium-{_worst_severity(result)}"]
    return pf.Div(summary, pf.BulletList(*items), classes=classes)


def _text_with_linebreaks(text: str) -> list:
    lines = text.splitlines() or [text]
    inlines: list = []
    for i, line in enumerate(lines):
        if i:
            inlines.append(pf.LineBreak())
        inlines.append(pf.Str(line))
    return inlines


def _tool_error_block(error: ToolError) -> pf.Div:
    heading = pf.Para(pf.Strong(pf.Str("allium check could not run:")))
    body = pf.Para(*_text_with_linebreaks(error.detail))
    blocks = [heading, body]
    if error.hint:
        blocks.append(pf.Para(pf.Str("Fix:"), pf.Space, pf.Code(error.hint)))
    return pf.Div(*blocks, classes=["allium-diagnostics", "allium-tool-error"])
