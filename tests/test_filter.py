import panflute as pf

from pandoc_allium import filter as allium_filter
from pandoc_allium.allium_cli import CheckResult, Diagnostic, ToolError


def make_doc():
    return pf.Doc(pf.Para(pf.Str("placeholder")))


def test_non_allium_code_block_is_left_untouched():
    elem = pf.CodeBlock("print(1)", classes=["python"])
    assert allium_filter.action(elem, make_doc()) is None


def test_non_code_block_elements_are_ignored():
    elem = pf.Para(pf.Str("hello"))
    assert allium_filter.action(elem, make_doc()) is None


def test_no_check_class_skips_allium_entirely(monkeypatch):
    called = False

    def fake_run_check(source, timeout=15.0):
        nonlocal called
        called = True
        return CheckResult()

    monkeypatch.setattr(allium_filter, "run_check", fake_run_check)
    elem = pf.CodeBlock("garbage", classes=["allium", "no-check"])
    result = allium_filter.action(elem, make_doc())
    assert result is None
    assert called is False


def test_clean_check_result_returns_none_no_extra_block(monkeypatch):
    monkeypatch.setattr(allium_filter, "run_check", lambda source, timeout=15.0: CheckResult())
    elem = pf.CodeBlock("entity Widget {}", classes=["allium"])
    result = allium_filter.action(elem, make_doc())
    assert result is None


def test_diagnostics_are_appended_after_the_untouched_code_block(monkeypatch):
    diag = Diagnostic(severity="error", message="boom", line=1, col=1, code="allium.x")
    monkeypatch.setattr(
        allium_filter, "run_check", lambda source, timeout=15.0: CheckResult(diagnostics=[diag])
    )
    elem = pf.CodeBlock("entity Widget {}", classes=["allium"])
    result = allium_filter.action(elem, make_doc())

    assert result is not None
    assert len(result) == 2
    assert result[0] is elem
    assert elem.text == "entity Widget {}"
    assert isinstance(result[1], pf.Div)
    assert "allium-diagnostics" in result[1].classes
    assert "allium-error" in result[1].classes


def test_tool_error_is_rendered_and_code_block_is_still_kept(monkeypatch):
    error = ToolError(kind="not_installed", detail="not found", hint="brew install ...")
    monkeypatch.setattr(
        allium_filter, "run_check", lambda source, timeout=15.0: CheckResult(error=error)
    )
    elem = pf.CodeBlock("entity Widget {}", classes=["allium"])
    result = allium_filter.action(elem, make_doc())

    assert result[0] is elem
    assert "allium-tool-error" in result[1].classes
