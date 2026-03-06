"""Tests for the OpenClaw CLI adapter and its registration."""

from __future__ import annotations

from unittest.mock import patch

from benchmark.adapters import get_adapter
from benchmark.adapters.openclaw_cli import (
    VALID_CONDITIONS,
    OpenClawCLIAdapter,
)
from benchmark.config import RunConfig
from benchmark.run import _resolve_settle_seconds, _validate_condition


def test_run_config_has_openclaw_timeout() -> None:
    cfg = RunConfig(agent="openclaw")
    assert cfg.answer_model is None
    assert cfg.openclaw_timeout == 120
    assert cfg.agent_id is None
    assert cfg.condition is None
    assert cfg.flush_sessions is False
    assert cfg.judge_concurrency == 4


def test_get_adapter_openclaw_returns_correct_type() -> None:
    adapter = get_adapter("openclaw")
    assert isinstance(adapter, OpenClawCLIAdapter)


def test_get_adapter_openclaw_with_config() -> None:
    cfg = RunConfig(
        agent="openclaw",
        agent_id="my-agent",
        openclaw_timeout=60,
        condition="cortex",
        flush_sessions=True,
    )
    adapter = get_adapter("openclaw", config=cfg)
    assert isinstance(adapter, OpenClawCLIAdapter)
    assert adapter._agent_id == "my-agent"
    assert adapter._timeout == 60
    assert adapter._condition == "cortex"
    assert adapter._flush_sessions is True


def test_openclaw_adapter_name_with_agent_id() -> None:
    adapter = OpenClawCLIAdapter(agent_id="test-agent")
    assert adapter.name == "openclaw:test-agent"

    adapter_no_id = OpenClawCLIAdapter()
    assert adapter_no_id.name == "openclaw"


def test_openclaw_adapter_handles_missing_executable() -> None:
    adapter = OpenClawCLIAdapter()
    with patch("benchmark.adapters.openclaw_cli.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("not found")
        result = adapter._call("hello")
    assert result["response"] is None
    assert "not found" in result["error"]
    assert "duration_ms" in result


def test_openclaw_adapter_parse_payloads() -> None:
    raw = '{"result": {"payloads": [{"text": "Hello world"}]}}'
    parsed = OpenClawCLIAdapter._parse_response(raw)
    assert parsed["response"] == "Hello world"


def test_openclaw_adapter_parse_text_fallback() -> None:
    raw = '{"text": "fallback text"}'
    parsed = OpenClawCLIAdapter._parse_response(raw)
    assert parsed["response"] == "fallback text"


def test_openclaw_adapter_parse_non_json() -> None:
    raw = "plain text response"
    parsed = OpenClawCLIAdapter._parse_response(raw)
    assert parsed["response"] == "plain text response"


def test_openclaw_adapter_parse_extracts_tool_names() -> None:
    raw = (
        '{"result": {"payloads": [{"text": "ok"}], '
        '"meta": {"systemPromptReport": {"tools": {"entries": '
        '[{"name": "cortex_search_memory"}, '
        '{"name": "cortex_save_memory"}]}}}}}'
    )
    parsed = OpenClawCLIAdapter._parse_response(raw)
    assert parsed["response"] == "ok"
    assert "cortex_search_memory" in parsed["tool_names"]
    assert "cortex_save_memory" in parsed["tool_names"]


def test_openclaw_adapter_predict_captures_error() -> None:
    adapter = OpenClawCLIAdapter()
    task = {"id": "t1", "input": "What color?"}
    with patch.object(adapter, "_call") as mock_call:
        mock_call.return_value = {
            "response": None,
            "error": "openclaw executable not found",
            "duration_ms": 5,
        }
        result = adapter.predict(task)
    assert result["output"] == ""
    assert "not found" in result["metadata"]["error"]
    assert result["metadata"]["duration_ms"] == 5


def test_openclaw_adapter_predict_cortex_date_injection() -> None:
    adapter = OpenClawCLIAdapter(condition="cortex")
    task = {
        "id": "t1",
        "input": "What happened?",
        "metadata": {"question_date": "2026/03/04 (Wed) 15:00"},
    }
    with patch.object(adapter, "_call") as mock_call:
        mock_call.return_value = {
            "response": "stuff",
            "duration_ms": 10,
        }
        adapter.predict(task)
    sent_msg = mock_call.call_args.args[0]
    assert "[cortex-date: 2026-03-04]" in sent_msg
    assert "What happened?" in sent_msg


def test_openclaw_adapter_predict_cortex_no_date() -> None:
    """Probe without question_date should skip date injection."""
    adapter = OpenClawCLIAdapter(condition="cortex")
    task = {"id": "t1", "input": "What happened?", "metadata": {}}
    with patch.object(adapter, "_call") as mock_call:
        mock_call.return_value = {"response": "stuff", "duration_ms": 10}
        adapter.predict(task)
    sent_msg = mock_call.call_args.args[0]
    assert "[cortex-date:" not in sent_msg


def test_openclaw_adapter_seed_cortex_date_injection() -> None:
    """Seed phase should inject haystack_dates into first user turn."""
    adapter = OpenClawCLIAdapter(condition="cortex")
    task = {
        "id": "t1",
        "input": "probe",
        "metadata": {
            "haystack_sessions": [
                [
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "hello"},
                ]
            ],
            "haystack_dates": ["2026/02/20 (Fri) 14:43"],
        },
    }
    with patch.object(adapter, "_call") as mock_call:
        mock_call.return_value = {"response": "ok", "duration_ms": 10}
        adapter.seed(task)
    sent_msg = mock_call.call_args_list[0].args[0]
    assert "2026-02-20" in sent_msg
    assert "hi" in sent_msg


def test_parse_dataset_date() -> None:
    assert OpenClawCLIAdapter._parse_dataset_date("2026/02/20 (Fri) 14:43") == "2026-02-20"
    assert OpenClawCLIAdapter._parse_dataset_date("2026/03/04 (Wed) 15:00") == "2026-03-04"
    assert OpenClawCLIAdapter._parse_dataset_date("bad format") is None
    assert OpenClawCLIAdapter._parse_dataset_date("") is None


def test_openclaw_adapter_seed_skips_assistant_turns() -> None:
    adapter = OpenClawCLIAdapter()
    task = {
        "id": "t1",
        "input": "probe",
        "metadata": {
            "haystack_sessions": [
                [
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "hello"},
                    {"role": "user", "content": "bye"},
                ]
            ]
        },
    }
    with patch.object(adapter, "_call") as mock_call:
        mock_call.return_value = {
            "response": "ok",
            "duration_ms": 10,
        }
        result = adapter.seed(task)
        calls = [c.args[0] for c in mock_call.call_args_list]
    assert calls == ["hi", "bye"]
    assert result["turn_count"] == 2
    assert result["total_duration_ms"] == 20


def test_openclaw_adapter_flush_sessions() -> None:
    adapter = OpenClawCLIAdapter(flush_sessions=True)
    task = {
        "id": "t1",
        "input": "probe",
        "metadata": {
            "haystack_sessions": [
                [{"role": "user", "content": "hi"}],
            ]
        },
    }
    with patch.object(adapter, "_call") as mock_call:
        mock_call.return_value = {
            "response": "ok",
            "duration_ms": 10,
        }
        adapter.seed(task)
        # Should have 2 calls: 1 user turn + 1 /new flush
        assert mock_call.call_count == 2
        assert mock_call.call_args_list[1].args[0] == "/new"


def test_condition_validation() -> None:
    # Valid conditions should not raise
    for cond in VALID_CONDITIONS:
        _validate_condition(cond)
    _validate_condition(None)

    # Invalid condition should raise
    import pytest

    with pytest.raises(ValueError, match="--condition must be"):
        _validate_condition("invalid")


def test_condition_aware_settle_defaults() -> None:
    assert _resolve_settle_seconds(None, "cortex") == 180
    assert _resolve_settle_seconds(None, "baseline") == 10
    assert _resolve_settle_seconds(None, "clawvault") == 10
    assert _resolve_settle_seconds(None, None) == 120
    # Explicit override wins
    assert _resolve_settle_seconds(30, "cortex") == 30


def test_dry_run_generates_random_judge_scores() -> None:
    from benchmark.judge import judge_all

    cfg = RunConfig(agent="local_stub", dry_run=True)
    tasks = [
        {"id": "t1", "input": "q1", "reference_answer": "a1"},
        {"id": "t2", "input": "q2", "reference_answer": "a2"},
    ]
    preds = [
        {"task_id": "t1", "output": "out1"},
        {"task_id": "t2", "output": "out2"},
    ]
    judgments = judge_all(tasks, preds, cfg)
    assert len(judgments) == 2
    for j in judgments:
        assert j["score"] in (0, 1, 2, 3)
        assert "[dry-run]" in j["rationale"]


def test_judge_parse_strips_code_fences() -> None:
    from benchmark.judge import _parse_judge_json

    raw = '```json\n{"score": 3, "rationale": "good"}\n```'
    result = _parse_judge_json(raw)
    assert result["score"] == 3
