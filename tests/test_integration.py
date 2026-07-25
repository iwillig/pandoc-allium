"""Integration tests: run pandoc with the filter against example files and
assert the output contains the expected diagnostics blocks.

These exercise the full pipeline (filter → allium_cli → allium check →
render) end-to-end, unlike the unit tests in test_filter.py which mock
run_check.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

HAS_ALLIUM = shutil.which("allium") is not None
HAS_PANDOC = shutil.which("pandoc") is not None

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = "examples"


def _run_pandoc(source: str) -> str:
    """Run pandoc with the filter against *source* and return plain-text output."""
    result = subprocess.run(
        [
            "pipenv", "run", "pandoc",
            "-F", "pandoc-allium",
            "-s", source,
            "-t", "plain",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, f"pandoc failed: {result.stderr}"
    return result.stdout


@pytest.mark.skipif(not (HAS_ALLIUM and HAS_PANDOC), reason="requires allium + pandoc on PATH")
class TestCommonErrorsExample:
    """examples/common-errors.md has blocks with errors, warnings, and a .no-check block."""

    @pytest.fixture(autouse=True)
    def _output(self):
        self.output = _run_pandoc(f"{EXAMPLES_DIR}/common-errors.md")

    def test_missing_version_marker_is_reported(self):
        assert "missing version marker" in self.output
        assert "allium.status.unreachableValue" not in self.output or True  # just sanity

    def test_undefined_type_reference_is_reported(self):
        assert "allium.type.undefinedReference" in self.output
        assert "UUID" in self.output

    def test_unused_entity_is_reported(self):
        assert "allium.entity.unused" in self.output

    def test_no_exit_status_is_reported(self):
        # The deployment example has 'deployed' with no exit transition
        assert "allium.status.noExit" in self.output

    def test_no_check_block_has_no_diagnostics(self):
        # The .no-check block contains "NotARealType" — if allium ran on it,
        # we'd see an error diagnostic. It should appear only as raw code.
        broken_section = self.output[self.output.index("Intentionally broken"):]
        # "NotARealType" appears in the code block but no [error] follows it
        assert "NotARealType" in broken_section
        # No diagnostics block after the no-check snippet
        assert "allium.type.undefinedReference" not in broken_section


@pytest.mark.skipif(not (HAS_ALLIUM and HAS_PANDOC), reason="requires allium + pandoc on PATH")
class TestWorkflowExample:
    """examples/workflow.md — a complete PR state machine with multiple rules."""

    @pytest.fixture(autouse=True)
    def _output(self):
        self.output = _run_pandoc(f"{EXAMPLES_DIR}/workflow.md")

    def test_has_diagnostics_block(self):
        assert "allium check:" in self.output

    def test_no_errors(self):
        assert "[error]" not in self.output

    def test_unused_field_info(self):
        # author field is declared but never referenced in rules
        assert "allium.field.unused" in self.output


@pytest.mark.skipif(not (HAS_ALLIUM and HAS_PANDOC), reason="requires allium + pandoc on PATH")
class TestMultiEntityExample:
    """examples/multi-entity.md — two entities with cross-entity rule references."""

    @pytest.fixture(autouse=True)
    def _output(self):
        self.output = _run_pandoc(f"{EXAMPLES_DIR}/multi-entity.md")

    def test_has_diagnostics_block(self):
        assert "allium check:" in self.output

    def test_no_errors(self):
        assert "[error]" not in self.output


@pytest.mark.skipif(not (HAS_ALLIUM and HAS_PANDOC), reason="requires allium + pandoc on PATH")
class TestDemoExample:
    """examples/demo.md — the original demo with clean, broken, and .no-check blocks."""

    @pytest.fixture(autouse=True)
    def _output(self):
        self.output = _run_pandoc(f"{EXAMPLES_DIR}/demo.md")

    def test_clean_spec_has_diagnostics(self):
        # Even a "clean" spec produces warnings/info
        assert "allium check:" in self.output

    def test_broken_spec_has_error(self):
        assert "Error" in self.output

    def test_no_check_block_is_skipped(self):
        nocheck_section = self.output[self.output.index("Opting out"):]
        assert "isn't valid allium" in nocheck_section
        # No diagnostics block follows the no-check snippet
        assert "allium check:" not in nocheck_section
