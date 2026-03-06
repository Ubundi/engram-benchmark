"""Tests for judge JSON parsing and scoring logic."""

import pytest

from benchmark.judge import _SYSTEM_PROMPT, _parse_judge_json


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


class TestJudgePrompt:
    def test_prompt_requires_specific_detail_for_score_3(self):
        assert "required specific detail" in _SYSTEM_PROMPT
        assert "if the required specific detail is absent, use 2, not 3" in _SYSTEM_PROMPT

    def test_prompt_treats_mixed_wrong_specific_answers_as_zero(self):
        assert "mixes relevant context with an incorrect specific answer" in _SYSTEM_PROMPT
        assert "if the response makes a concrete but wrong claim, use 0, not 1" in _SYSTEM_PROMPT

    def test_prompt_restricts_judging_scope(self):
        assert "Judge the response only against the question, ground truth, and agent response" in _SYSTEM_PROMPT
