"""Pandoc filter entry point: `pandoc -F pandoc-allium ...`

For every fenced code block written as:

    ```allium
    -- allium: 1
    entity Order { ... }
    ```

this runs `allium check` against the block's contents and inserts a
diagnostics report right after it. The code block itself is never
rewritten -- pass `--syntax-definition pandoc_allium/syntax/allium.xml` to
pandoc alongside this filter to also get native Skylighting syntax
highlighting, in any output format.

Add `.no-check` to the block's classes (```` ```{.allium .no-check} ````)
to skip invoking allium entirely, e.g. for intentionally-invalid snippets
in documentation.
"""

from __future__ import annotations

import panflute as pf

from .allium_cli import run_check
from .render import diagnostics_block

SKIP_CLASSES = {"no-check", "nocheck"}


def action(elem: pf.Element, doc: pf.Doc):
    if not isinstance(elem, pf.CodeBlock) or "allium" not in elem.classes:
        return None

    if SKIP_CLASSES & set(elem.classes):
        return None

    result = run_check(elem.text)
    if result.error is not None:
        pf.debug(f"[pandoc-allium] {result.error.kind}: {result.error.detail}")

    diag = diagnostics_block(result)
    return None if diag is None else [elem, diag]


def main(doc: pf.Doc = None) -> None:
    pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
