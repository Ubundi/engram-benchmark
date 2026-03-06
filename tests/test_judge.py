"""Tests for judge JSON parsing and scoring logic."""

import pytest

from benchmark.judge import _parse_judge_json


class TestParseJudgeJson:
    def test_plain_json(self):
        result = _parse_judge_json('{"score": 3, "rationale": "correct"}')
        assert result["score"] == 3
        assert result["rationale"] == "correct"

    def test_code_fenced_json(self):
        raw = '```json\n{"score": 2, "rationale": "partial"}\n```'
        result = _parse_judge_json(raw)
        assert result["score"] == 2

    def test_json_with_surrounding_text(self):
        raw = 'Here is my evaluation:\n{"score": 1, "rationale": "abstained"}\nDone.'
        result = _parse_judge_json(raw)
        assert result["score"] == 1

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="non-JSON"):
            _parse_judge_json("I think the score is 3")

    def test_invalid_json_raises(self):
        with pytest.raises((ValueError, Exception)):
            _parse_judge_json("{score: 3}")  # missing quotes

    def test_multiline_json(self):
        raw = '{\n  "score": 0,\n  "rationale": "hallucinated"\n}'
        result = _parse_judge_json(raw)
        assert result["score"] == 0
