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


def _sweep_arrays(population):
    """Per-customer truth and largest payment, in a fixed order, as numpy arrays."""
    labels, top = population.labels(), population.max_amount_by_customer()
    ids = sorted(labels)
    return np.array([labels[i] for i in ids]), np.array([top[i] for i in ids])


def _numpy_costs(y_true, amounts, thresholds, fn_cost):
    """fn_cost*FN + FP at every threshold, vectorised -- no fc-10 code involved."""
    alerts = amounts[None, :] > np.asarray(thresholds, dtype=float)[:, None]
    fn = (~alerts & y_true[None, :]).sum(axis=1)
    fp = (alerts & ~y_true[None, :]).sum(axis=1)
    return fn_cost * fn + fp


def _numpy_argmin(thresholds, costs):
    """Lowest cost; ties to the HIGHER threshold (fewer alerts for the same cost)."""
    best = costs.min()
    return max(t for t, c in zip(thresholds, costs) if c == best)


def test_the_studio_sweep_matches_sklearn_at_every_grid_point(population):
    # Week 3: the sweep is its own implementation (sorted maxima + bisect), so
    # it needs its own oracle -- sklearn at EVERY point on the curve.
    from tools.tm_sim_source import fc10_module
    sweep = fc10_module("runtime.manufacturing.tuning.sweep")
    y_true, amounts = _sweep_arrays(population)
    points = sweep.run(population, "high_value")["points"]
    assert len(points) >= 50, "a sweep of %d points is not a curve" % len(points)
    caught = 0
    for p in points:
        ref = _sklearn(y_true, amounts > p["threshold"])
        for k in ("tp", "fp", "fn", "tn"):
            assert p[k] == ref[k], (p["threshold"], k)
        for k in ("recall", "fpr"):
            assert p[k] == pytest.approx(ref[k], abs=1e-6), (p["threshold"], k)
        if p["alerts"]:
            assert p["precision"] == pytest.approx(ref["precision"], abs=1e-6), p["threshold"]
            caught += p["tp"] > 0
    assert caught >= 50


@pytest.mark.parametrize("ratio", (2, 5, 9, 11, 20, 50))
def test_the_cost_weighted_optimum_matches_a_numpy_argmin(population, ratio):
    from tools.tm_sim_source import fc10_module
    sweep = fc10_module("runtime.manufacturing.tuning.sweep")
    result = sweep.run(population, "high_value")
    thresholds = [p["threshold"] for p in result["points"]]
    y_true, amounts = _sweep_arrays(population)
    expected = _numpy_argmin(thresholds, _numpy_costs(y_true, amounts, thresholds, ratio))
    assert sweep.cost_weighted_best(result, fn_cost=ratio, fp_cost=1)["point"]["threshold"] == expected


def test_decision_1s_dominance_claim_holds_in_numpy(population):
    """D1 held high_value at GBP 75,000 on the claim that it is cost-optimal for
    NO FN:FP ratio from 1 to 100. Re-derived here from the raw population with
    numpy alone, so the decision does not rest on one implementation."""
    from tools.tm_sim_source import fc10_module
    sweep = fc10_module("runtime.manufacturing.tuning.sweep")
    log = fc10_module("runtime.manufacturing.tuning.decision_log")
    [d1] = [e for e in log.load() if e["decision_id"] == "D1"]
    thresholds = [p["threshold"] for p in sweep.run(population, "high_value")["points"]]
    y_true, amounts = _sweep_arrays(population)

    ranges = []
    for i in range(991):                       # FN:FP 1.0 .. 100.0 in 0.1 steps
        k = round(1.0 + i * 0.1, 6)
        t = _numpy_argmin(thresholds, _numpy_costs(y_true, amounts, thresholds, k))
        if ranges and ranges[-1]["threshold"] == t:
            ranges[-1]["fn_fp_to"] = k
        else:
            ranges.append({"threshold": t, "fn_fp_from": k, "fn_fp_to": k})

    assert len(ranges) >= 5
    assert d1["from_threshold"] not in {r["threshold"] for r in ranges}, "75k IS optimal somewhere"
    assert ranges == d1["evidence"]["cost_optimal_ranges"]


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
