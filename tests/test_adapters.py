"""Tests for adapter interface and local stub implementation."""

import pytest

from benchmark.adapters.base import BaseAdapter
from benchmark.adapters.local_stub import LocalStubAdapter


class TestBaseAdapterContract:
    """Verify that BaseAdapter enforces the required interface."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseAdapter()

    def test_must_implement_name(self):
        class BadAdapter(BaseAdapter):
            def predict(self, task):
                return {"output": ""}

        with pytest.raises(TypeError):
            BadAdapter()

    def test_must_implement_predict(self):
        class BadAdapter(BaseAdapter):
            @property
            def name(self):
                return "bad"

        with pytest.raises(TypeError):
            BadAdapter()

    def test_default_seed_is_noop(self):
        class MinimalAdapter(BaseAdapter):
            @property
            def name(self):
                return "minimal"

            def predict(self, task):
                return {"output": ""}

        adapter = MinimalAdapter()
        result = adapter.seed({"id": "t1"})
        assert result["seeded"] is False
        assert result["session_count"] == 0


class TestLocalStubAdapter:
    def setup_method(self):
        self.adapter = LocalStubAdapter()

    def test_name(self):
        assert self.adapter.name == "local_stub"

    def test_predict_returns_reference_answer(self):
        task = {
            "id": "t1",
            "input": "What is 2+2?",
            "reference_answer": "4",
        }
        result = self.adapter.predict(task)
        assert result["output"] == "4"
        assert result["metadata"]["deterministic"] is True

    def test_predict_without_reference_answer(self):
        task = {"id": "t1", "input": "What is 2+2?"}
        result = self.adapter.predict(task)
        assert result["output"].startswith("stub:t1:")
        assert len(result["metadata"]["digest"]) == 8

    def test_predict_is_deterministic(self):
        task = {"id": "t1", "input": "same question"}
        r1 = self.adapter.predict(task)
        r2 = self.adapter.predict(task)
        assert r1["output"] == r2["output"]
        assert r1["metadata"]["digest"] == r2["metadata"]["digest"]

    def test_predict_different_inputs_different_digests(self):
        t1 = {"id": "t1", "input": "question A"}
        t2 = {"id": "t1", "input": "question B"}
        r1 = self.adapter.predict(t1)
        r2 = self.adapter.predict(t2)
        assert r1["metadata"]["digest"] != r2["metadata"]["digest"]

    def test_seed_counts_sessions(self):
        task = {
            "id": "t1",
            "metadata": {
                "haystack_sessions": [
                    [{"role": "user", "content": "hi"}],
                    [{"role": "user", "content": "hello"}],
                ],
            },
        }
        result = self.adapter.seed(task)
        assert result["seeded"] is True
        assert result["session_count"] == 2

    def test_seed_no_sessions(self):
        task = {"id": "t1", "metadata": {}}
        result = self.adapter.seed(task)
        assert result["seeded"] is True
        assert result["session_count"] == 0
