"""The training workspace is the Tuning Studio's independent oracle.

fc-10 computes precision, recall, FPR and F1 by hand so it can stay free of
scikit-learn. Here the same numbers are computed with sklearn on the same
TM-SIM population, and they must agree. A hand-rolled metric that drifts from
the textbook definition goes red here, not in a tuning paper.

This test FAILS, rather than skips, when fc-10 cannot be found: a parity check
that skips on a missing oracle passes by checking nothing.

One agreed difference: where a denominator is zero, sklearn returns 0.0 (with
zero_division=0) and fc-10 returns None. Asserted explicitly below, so the
difference is a documented decision rather than an unnoticed mismatch.
"""
import numpy as np
import pytest
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

from tools.tm_sim_source import load

tm_sim, metrics = load()

THRESHOLDS = (25_000, 50_000, 75_000, 100_000, 250_000)


@pytest.fixture(scope="module")
def population():
    return tm_sim.generate()


def _sklearn(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[False, True]).ravel()
    return {
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "fpr": fp / (fp + tn),
    }


@pytest.mark.parametrize("threshold", THRESHOLDS)
def test_high_value_metrics_match_sklearn(population, threshold):
    labels, top = population.labels(), population.max_amount_by_customer()
    ids = sorted(labels)
    y_true = np.array([labels[i] for i in ids])
    y_pred = np.array([top[i] > threshold for i in ids])

    ours = metrics.evaluate(y_true.tolist(), y_pred.tolist())
    ref = _sklearn(y_true, y_pred)

    assert ours["tp"] > 0, "parity on a rule that caught nothing proves nothing"
    for k in ("tp", "fp", "fn", "tn"):
        assert ours[k] == ref[k], (k, ours[k], ref[k])
    for k in ("precision", "recall", "f1", "fpr"):
        assert ours[k] == pytest.approx(ref[k], abs=1e-12), (k, ours[k], ref[k])


def test_the_asymmetric_witness_matches_sklearn():
    y_true = [True, False, False, False, True] + [False] * 5
    y_pred = [True, True, True, True, False] + [False] * 5
    ours, ref = metrics.evaluate(y_true, y_pred), _sklearn(y_true, y_pred)
    assert (ours["tp"], ours["fp"], ours["fn"], ours["tn"]) == (ref["tp"], ref["fp"], ref["fn"], ref["tn"])
    assert ours["precision"] == pytest.approx(ref["precision"])


def test_undefined_is_none_in_fc10_and_zero_in_sklearn():
    y_true, y_pred = [True, False, False], [False, False, False]
    assert metrics.evaluate(y_true, y_pred)["precision"] is None
    assert precision_score(y_true, y_pred, zero_division=0) == 0.0


def test_the_governed_backtest_matches_sklearn(population):
    # Week 2: the studio's backtest over the REGISTERED rule must agree with
    # sklearn computed from the raw population -- the backtest cannot agree
    # with itself while being wrong.
    from tools.tm_sim_source import fc10_module
    backtest = fc10_module("runtime.manufacturing.tuning.backtest")
    registry = fc10_module("runtime.manufacturing.data_model.tm_rule_registry")
    rule = registry.rule("high_value")
    got = backtest.evaluate_rule(population, rule)

    labels, top = population.labels(), population.max_amount_by_customer()
    ids = sorted(labels)
    ref = _sklearn([labels[i] for i in ids], [top[i] > rule["threshold"] for i in ids])
    assert got["tp"] > 0
    for k in ("tp", "fp", "fn", "tn"):
        assert got[k] == ref[k], k
    for k in ("precision", "recall", "f1", "fpr"):
        assert got[k] == pytest.approx(ref[k], abs=1e-6), k   # the backtest rounds to 6 dp
