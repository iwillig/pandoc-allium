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

For HTML output, include the bundled CSS for styled diagnostics:
  pandoc -s --css pandoc_allium/static/diagnostics.css ...
"""

from __future__ import annotations

from typing import Optional

import panflute as pf

from .allium_cli import CheckResult, Diagnostic, ToolError

SEVERITY_ICON = {"error": "✗", "warning": "⚠", "info": "ℹ"}
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
SEVERITY_LABEL = {"error": "Error", "warning": "Warning", "info": "Info"}


def _location(diag: Diagnostic) -> str:
    if diag.line is None:
        return ""
    if diag.col is None:
        return f"line {diag.line}"
    return f"line {diag.line}:{diag.col}"


def _location_span(diag: Diagnostic) -> Optional[pf.Span]:
    loc = _location(diag)
    if not loc:
        return None
    return pf.Span(pf.Str(loc), classes=["allium-location"])


def _code_span(code: str) -> pf.Span:
    return pf.Span(pf.Str(code), classes=["allium-code"])


def _diagnostic_item(diag: Diagnostic) -> pf.Span:
    inlines: list = []
    loc = _location_span(diag)
    if loc:
        inlines.append(loc)
        inlines.append(pf.Space)
    inlines.append(pf.Str(" ".join(diag.message.split())))
    if diag.code:
        inlines.append(pf.Space)
        inlines.append(_code_span(diag.code))
    return pf.Span(*inlines, classes=["allium-diagnostic-item"])


def _summary_text(result: CheckResult) -> str:
    counts = {"error": 0, "warning": 0, "info": 0}
    for d in result.diagnostics:
        counts[d.severity] = counts.get(d.severity, 0) + 1
    parts = [f"{n} {sev}{'s' if n != 1 else ''}" for sev, n in counts.items() if n]
    return ", ".join(parts) if parts else "no diagnostics"


def _worst_severity(result: CheckResult) -> str:
    if not result.diagnostics:
        return "info"
    return min((d.severity for d in result.diagnostics), key=lambda s: SEVERITY_ORDER.get(s, 9))


def _severity_groups(result: CheckResult) -> list[tuple[str, list[Diagnostic]]]:
    """Return (severity, diagnostics) groups in order, only for severities that have items."""
    groups: dict[str, list[Diagnostic]] = {}
    for d in result.diagnostics:
        groups.setdefault(d.severity, []).append(d)
    return [(sev, groups[sev]) for sev in SEVERITY_ORDER if sev in groups]


def diagnostics_block(result: CheckResult) -> Optional[pf.Div]:
    """Build the diagnostics Div, or None when there's nothing worth showing."""
    if result.error is not None:
        return _tool_error_block(result.error)

    if not result.diagnostics:
        return None

    worst = _worst_severity(result)
    summary = _summary_text(result)
    groups = _severity_groups(result)

    blocks: list = []

    # Header: icon + summary
    icon = SEVERITY_ICON.get(worst, "?")
    label = SEVERITY_LABEL.get(worst, worst.title())
    header_inlines: list = [
        pf.Str(f"{icon} "),
        pf.Strong(pf.Str(f"allium check: {label}")),
        pf.Str(f" — {summary}"),
    ]
    blocks.append(pf.Div(pf.Para(*header_inlines), classes=["allium-header"]))

    # Grouped diagnostics
    for sev, diags in groups:
        group_label = SEVERITY_LABEL.get(sev, sev.title())
        blocks.append(pf.Div(pf.Para(pf.Strong(pf.Str(group_label))), classes=["allium-group-label"]))
        items = [pf.ListItem(pf.Para(_diagnostic_item(d))) for d in diags]
        blocks.append(pf.BulletList(*items))

    classes = ["allium-diagnostics", f"allium-{worst}"]
    return pf.Div(*blocks, classes=classes)


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
