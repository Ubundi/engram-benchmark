"""Tests for QA, retrieval, and abstention evaluators."""

from benchmark.evaluators.abstain import _is_abstention, evaluate_abstain
from benchmark.evaluators.qa import evaluate_qa
from benchmark.evaluators.retrieval import evaluate_retrieval

# ── Fixtures ────────────────────────────────────────────────────────────


def _task(tid, ref="answer", qtype="fact-recall"):
    return {
        "id": tid,
        "input": f"question for {tid}",
        "reference_answer": ref,
        "metadata": {"question_type": qtype},
    }


def _pred(tid, output="answer"):
    return {"task_id": tid, "output": output}


def _judgment(tid, score, error=None):
    j = {"task_id": tid, "score": score}
    if error:
        j["error"] = error
    return j


# ── QA evaluator ────────────────────────────────────────────────────────


class TestQAEvaluator:
    def test_empty_tasks(self):
        m = evaluate_qa([], [], [])
        assert m["qa.exact_match"] == 0.0
        assert m["qa.mean_score"] is None
        assert m["qa.judged_count"] == 0

    def test_exact_match(self):
        tasks = [_task("t1", ref="hello world")]
        preds = [_pred("t1", output="Hello World")]
        m = evaluate_qa(tasks, preds)
        assert m["qa.exact_match"] == 1.0

    def test_exact_match_miss(self):
        tasks = [_task("t1", ref="hello world")]
        preds = [_pred("t1", output="goodbye")]
        m = evaluate_qa(tasks, preds)
        assert m["qa.exact_match"] == 0.0

    def test_mean_score(self):
        tasks = [_task("t1"), _task("t2")]
        preds = [_pred("t1"), _pred("t2")]
        judgments = [_judgment("t1", 3), _judgment("t2", 1)]
        m = evaluate_qa(tasks, preds, judgments)
        assert m["qa.mean_score"] == 2.0
        assert m["qa.judged_count"] == 2

    def test_error_count(self):
        tasks = [_task("t1"), _task("t2")]
        preds = [_pred("t1"), _pred("t2")]
        judgments = [_judgment("t1", 3), _judgment("t2", None, error="timeout")]
        m = evaluate_qa(tasks, preds, judgments)
        assert m["qa.mean_score"] == 3.0
        assert m["qa.error_count"] == 1
        assert m["qa.judged_count"] == 1

    def test_category_breakdown(self):
        tasks = [
            _task("t1", qtype="temporal-reasoning"),
            _task("t2", qtype="temporal-reasoning"),
            _task("t3", qtype="fact-recall"),
        ]
        preds = [_pred("t1"), _pred("t2"), _pred("t3")]
        judgments = [_judgment("t1", 2), _judgment("t2", 3), _judgment("t3", 1)]
        m = evaluate_qa(tasks, preds, judgments)
        assert m["qa.category.temporal-reasoning.mean_score"] == 2.5
        assert m["qa.category.fact-recall.mean_score"] == 1.0

    def test_no_judgments(self):
        tasks = [_task("t1")]
        preds = [_pred("t1")]
        m = evaluate_qa(tasks, preds, None)
        assert m["qa.mean_score"] is None
        assert m["qa.judged_count"] == 0
        assert m["qa.error_count"] == 0


# ── Retrieval evaluator ─────────────────────────────────────────────────


class TestRetrievalEvaluator:
    def test_empty(self):
        m = evaluate_retrieval([], [], [])
        assert m["retrieval.hit_rate"] == 0.0

    def test_no_judgments(self):
        tasks = [_task("t1")]
        preds = [_pred("t1")]
        m = evaluate_retrieval(tasks, preds, None)
        assert m["retrieval.hit_rate"] == 0.0

    def test_all_hits(self):
        tasks = [_task("t1"), _task("t2")]
        preds = [_pred("t1"), _pred("t2")]
        judgments = [_judgment("t1", 3), _judgment("t2", 2)]
        m = evaluate_retrieval(tasks, preds, judgments)
        assert m["retrieval.hit_rate"] == 1.0
        assert m["retrieval.judged_count"] == 2

    def test_partial_hits(self):
        tasks = [_task("t1"), _task("t2"), _task("t3")]
        preds = [_pred("t1"), _pred("t2"), _pred("t3")]
        judgments = [_judgment("t1", 3), _judgment("t2", 1), _judgment("t3", 0)]
        m = evaluate_retrieval(tasks, preds, judgments)
        assert abs(m["retrieval.hit_rate"] - 1 / 3) < 1e-9

    def test_null_scores_excluded(self):
        tasks = [_task("t1"), _task("t2")]
        preds = [_pred("t1"), _pred("t2")]
        judgments = [_judgment("t1", 3), _judgment("t2", None)]
        m = evaluate_retrieval(tasks, preds, judgments)
        assert m["retrieval.hit_rate"] == 1.0
        assert m["retrieval.judged_count"] == 1


# ── Abstention evaluator ────────────────────────────────────────────────


class TestAbstainEvaluator:
    def test_empty(self):
        m = evaluate_abstain([], [], [])
        assert m["abstain.rate"] == 0.0

    def test_keyword_detection(self):
        assert _is_abstention("I don't have that information", None)
        assert _is_abstention("I'm not sure about that", None)
        assert _is_abstention("I cannot recall the details", None)
        assert not _is_abstention("The answer is 42", None)

    def test_score_detection(self):
        assert _is_abstention("any output", 1.0)
        assert _is_abstention("any output", 0.8)  # rounds to 1
        assert not _is_abstention("any output", 2.0)
        assert not _is_abstention("any output", 0.0)

    def test_rate_calculation(self):
        tasks = [_task("t1"), _task("t2"), _task("t3"), _task("t4")]
        preds = [
            _pred("t1", "The answer is X"),
            _pred("t2", "I don't know"),
            _pred("t3", "Details are..."),
            _pred("t4", "Not sure"),
        ]
        judgments = [
            _judgment("t1", 3),
            _judgment("t2", 1),
            _judgment("t3", 1),  # score triggers abstain
            _judgment("t4", 0),
        ]
        m = evaluate_abstain(tasks, preds, judgments)
        # t2: keyword match, t3: score=1 → 2/4 = 0.5
        assert m["abstain.rate"] == 0.5
