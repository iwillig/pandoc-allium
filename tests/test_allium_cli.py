import shutil
import stat

import pytest

from pandoc_allium import allium_cli

HAS_ALLIUM = shutil.which("allium") is not None

CLEAN_SPEC = """\
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
"""

BROKEN_SPEC = """\
entity Order {
    id: UUID
}
"""


def make_fake_binary(tmp_path, script: str) -> str:
    path = tmp_path / "fake-allium"
    path.write_text(script)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


@pytest.mark.skipif(not HAS_ALLIUM, reason="requires the real `allium` CLI on PATH")
def test_clean_spec_has_no_errors_and_no_tool_error():
    result = allium_cli.run_check(CLEAN_SPEC)
    assert result.error is None
    assert not result.has_errors


@pytest.mark.skipif(not HAS_ALLIUM, reason="requires the real `allium` CLI on PATH")
def test_broken_spec_reports_an_error_diagnostic_with_location():
    result = allium_cli.run_check(BROKEN_SPEC)
    assert result.error is None
    assert result.has_errors
    errors = [d for d in result.diagnostics if d.severity == "error"]
    assert any(d.code == "allium.type.undefinedReference" for d in errors)
    assert errors[0].line is not None
    assert errors[0].col is not None


def test_missing_binary_is_a_not_installed_tool_error(monkeypatch):
    monkeypatch.setenv("ALLIUM_BIN", "/no/such/allium-binary")
    result = allium_cli.run_check(CLEAN_SPEC)
    assert result.diagnostics == []
    assert result.error is not None
    assert result.error.kind == "not_installed"
    assert "brew install" in result.error.hint


def test_timeout_is_reported_as_a_timeout_tool_error(tmp_path, monkeypatch):
    fake = make_fake_binary(tmp_path, "#!/bin/sh\nsleep 5\n")
    monkeypatch.setenv("ALLIUM_BIN", fake)
    result = allium_cli.run_check(CLEAN_SPEC, timeout=0.2)
    assert result.diagnostics == []
    assert result.error is not None
    assert result.error.kind == "timeout"


def test_non_json_stdout_is_an_invalid_output_tool_error(tmp_path, monkeypatch):
    fake = make_fake_binary(tmp_path, "#!/bin/sh\necho 'not json'\nexit 0\n")
    monkeypatch.setenv("ALLIUM_BIN", fake)
    result = allium_cli.run_check(CLEAN_SPEC)
    assert result.diagnostics == []
    assert result.error is not None
    assert result.error.kind == "invalid_output"


def test_json_without_diagnostics_array_is_an_invalid_output_tool_error(tmp_path, monkeypatch):
    fake = make_fake_binary(tmp_path, "#!/bin/sh\necho '{\"command\": \"check\"}'\nexit 0\n")
    monkeypatch.setenv("ALLIUM_BIN", fake)
    result = allium_cli.run_check(CLEAN_SPEC)
    assert result.error is not None
    assert result.error.kind == "invalid_output"


def test_stderr_only_failure_is_surfaced_as_runtime_error(tmp_path, monkeypatch):
    fake = make_fake_binary(
        tmp_path, "#!/bin/sh\necho 'boom: disk on fire' 1>&2\nexit 1\n"
    )
    monkeypatch.setenv("ALLIUM_BIN", fake)
    result = allium_cli.run_check(CLEAN_SPEC)
    assert result.error is not None
    assert result.error.kind == "runtime_error"
    assert "boom" in result.error.detail
