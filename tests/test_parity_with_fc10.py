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


# ---------------------------------------------------------------------------
# Week 4 -- capacity. An INDEPENDENT queue, written from the documented rules and
# not from fc-10's code: whole-number arithmetic in tenths of a review (no
# Fraction), a plain list as the queue, pandas for the workload. The rules:
#   * one alert per (customer, calendar month), dated to its first payment over
#     the line; same-day alerts queue in customer-id order;
#   * reviews happen Monday-Friday only; a weekend alert is received Monday;
#   * each working day adds `capacity` to a credit; whole units of credit work
#     the oldest alerts; an EMPTY queue drops whole unused credit (no banking);
#   * a wait is working days from the first day an alert could be worked.
# ---------------------------------------------------------------------------
import datetime as _dt

import pandas as pd


_FRAMES = {}


def _frame(population):
    key = id(population)   # frozen, module-scoped; digest() re-serialises 180k rows
    if key not in _FRAMES:
        _FRAMES[key] = pd.DataFrame([(t.customer_id, t.value_date, t.amount) for t in population.transactions],
                                    columns=["customer", "date", "amount"])
    return _FRAMES[key]


def _cm_alerts(population, threshold):
    """(date, customer) per customer-month alert, in queue order -- via pandas."""
    df = _frame(population)
    over = df[df.amount > threshold].copy()
    over["month"] = over.date.str[:7]
    first = over.groupby(["customer", "month"]).date.min().reset_index()
    return sorted(zip(first.date, first.customer))


_CM_MAX = {}


def _cm_workload(population, threshold):
    """Customer-month alerts at a threshold = months whose LARGEST payment is over
    it. One pandas group-by per population, cached; each threshold is a compare."""
    key = id(population)   # frozen, module-scoped; digest() re-serialises 180k rows
    if key not in _CM_MAX:
        df = pd.DataFrame([(t.customer_id, t.value_date[:7], t.amount) for t in population.transactions],
                          columns=["customer", "month", "amount"])
        _CM_MAX[key] = df.groupby(["customer", "month"]).amount.max().to_numpy()
    return int((_CM_MAX[key] > threshold).sum())


def _window(population):
    start = _dt.date.fromisoformat(population.params["start"])
    days, d = [], start
    months = population.params["months"]
    end_y, end_m = divmod(start.month - 1 + months, 12)
    end = _dt.date(start.year + end_y, end_m + 1, 1)
    while d < end:
        days.append(d)
        d += _dt.timedelta(days=1)
    return days


def _independent_queue(population, threshold, capacity, sla=None):
    """Returns (backlog_end, waits, caught_planted_customers)."""
    tenths = round(capacity * 10)
    arrivals = {}
    for date, cust in _cm_alerts(population, threshold):
        arrivals.setdefault(date, []).append(cust)
    labels = population.labels()
    queue, credit, workday, waits, caught = [], 0, -1, [], set()
    for day in _window(population):
        working = day.weekday() < 5
        if working:
            workday += 1
        received = workday if working else workday + 1
        queue += [(c, received) for c in arrivals.get(day.isoformat(), [])]
        if working:
            credit += tenths
            while queue and credit >= 10:
                cust, rec = queue.pop(0)
                credit -= 10
                waits.append(workday - rec)
                if labels[cust] and (sla is None or workday - rec <= sla):
                    caught.add(cust)
            if not queue:
                credit %= 10
    return len(queue), waits, caught


@pytest.mark.parametrize("threshold,cap", [(75_000, 2.0), (177_500, 2.0), (122_500, 4.0), (100_000, 0.7)])
def test_the_capacity_queue_matches_an_independent_one(population, threshold, cap):
    from tools.tm_sim_source import fc10_module
    capacity = fc10_module("runtime.manufacturing.tuning.capacity")
    q = capacity.simulate_queue(capacity.daily_arrivals(population, threshold),
                                capacity.calendar(population), cap)
    backlog, waits, _caught = _independent_queue(population, threshold, cap)
    assert q["worked"] > 0, "a queue that worked nothing proves nothing"
    assert q["backlog_end"] == backlog
    assert sorted(q["waits"]) == sorted(waits)


@pytest.mark.parametrize("threshold,cap,sla", [(75_000, 2.0, None), (75_000, 2.0, 10),
                                                (177_500, 2.0, 10), (122_500, 4.0, None)])
def test_effective_recall_matches_an_independent_queue(population, threshold, cap, sla):
    from tools.tm_sim_source import fc10_module
    capacity = fc10_module("runtime.manufacturing.tuning.capacity")
    _b, _w, caught = _independent_queue(population, threshold, cap, sla)
    planted = sum(population.labels().values())
    got = capacity.effective_recall(population, threshold, cap, sla_working_days=sla)
    assert got == pytest.approx(len(caught) / planted, abs=1e-6)


def test_the_frontier_workload_matches_pandas_and_unlimited_capacity_matches_sklearn(population):
    from tools.tm_sim_source import fc10_module
    capacity = fc10_module("runtime.manufacturing.tuning.capacity")
    f = capacity.frontier(population, "high_value", 2.0)
    y_true, amounts = _sweep_arrays(population)
    for p in f["points"][::8]:
        assert p["workload"] == len(_cm_alerts(population, p["threshold"])), p["threshold"]
        assert p["workload"] == _cm_workload(population, p["threshold"]), p["threshold"]
    for t in (50_000, 75_000, 150_000):
        ref = recall_score(y_true, amounts > t)
        assert capacity.effective_recall(population, t, 10_000) == pytest.approx(ref, abs=1e-6)


def test_decision_2s_evidence_holds_under_the_independent_queue(population):
    """D2 held GBP 75,000 on: effective recall 0.135 (0 within the SLA) against
    0.325 at the capacity frontier, and a staffing need of ~1,390/day. Every one
    of those re-derived here from pandas and the independent queue."""
    from tools.tm_sim_source import fc10_module
    log = fc10_module("runtime.manufacturing.tuning.decision_log")
    [d2] = [e for e in log.load() if e["decision_id"] == "D2"]
    a, ev = d2["assumptions"], d2["evidence"]
    cap = a["bank_capacity_per_day"] / a["sample_ratio"]
    planted = sum(population.labels().values())
    budget = cap * sum(d.weekday() < 5 for d in _window(population))

    # The operating point: best recall whose customer-month workload fits.
    y_true, amounts = _sweep_arrays(population)
    grid = sorted({p["threshold"] for p in [ev["today"], ev["operating_point"]]} |
                  set(range(10_000, 200_001, 2_500)))
    fits = [(recall_score(y_true, amounts > t), t) for t in grid if _cm_workload(population, t) <= budget]
    assert max(fits)[1] == ev["operating_point"]["threshold"]

    for key in ("today", "operating_point"):
        t = ev[key]["threshold"]
        backlog, _w, caught = _independent_queue(population, t, cap)
        _b, _w2, caught_sla = _independent_queue(population, t, cap, a["sla_working_days"])
        assert ev[key]["workload"] == len(_cm_alerts(population, t))
        assert ev[key]["queue"]["backlog_end"] == backlog
        assert ev[key]["effective_recall"] == pytest.approx(len(caught) / planted, abs=1e-6)
        assert ev[key]["effective_recall_within_sla"] == pytest.approx(len(caught_sla) / planted, abs=1e-6)

    need = len(_cm_alerts(population, ev["today"]["threshold"])) / sum(d.weekday() < 5 for d in _window(population))
    assert ev["capacity_to_hold_today"]["bank_scale_per_day"] == pytest.approx(need * a["sample_ratio"], abs=0.1)


# -- week 5: Decision 3, re-derived by brute force ------------------------------

def _group_arrays(population, groups):
    """Per line: sorted customer-month top payments (workload) and sorted
    customer-level top payments of PLANTED customers (catches) -- pandas, not
    fc-10's curves."""
    import pandas as pd
    seg = {c.customer_id: c.segment for c in population.customers}
    line_of = {s: g for g, members in groups.items() for s in members}
    df = pd.DataFrame([(t.customer_id, t.value_date[:7], t.amount) for t in population.transactions],
                      columns=["cid", "month", "amount"])
    df["line"] = df["cid"].map(seg).map(line_of)
    cm = df.groupby(["line", "cid", "month"])["amount"].max().reset_index()
    top = df.groupby(["line", "cid"])["amount"].max().reset_index()
    planted = {c.customer_id for c in population.customers if c.planted}
    top = top[top["cid"].isin(planted)]
    return ({g: np.sort(cm.loc[cm.line == g, "amount"].to_numpy()) for g in groups},
            {g: np.sort(top.loc[top.line == g, "amount"].to_numpy()) for g in groups})


def _above(arr, t):
    return int(len(arr) - np.searchsorted(arr, t, side="right"))


def _caught(population, lines_by_segment):
    planted = [c for c in population.customers if c.planted]
    top = population.max_amount_by_customer()
    return sum(top[c.customer_id] > lines_by_segment[c.segment] for c in planted)


def test_decision_3_is_the_best_pair_of_lines_by_brute_force(population):
    """D3 chose retail 30,000 / non-retail 152,500 at D2's workload. Search EVERY
    pair of lines on the grid here, with pandas, and require the same answer and
    the same catches -- fitted and on the hold-out. fc-10 fits by a dynamic
    programme; a bug in that shortcut cannot hide behind itself."""
    from tools.tm_sim_source import fc10_module
    log = fc10_module("runtime.manufacturing.tuning.decision_log")
    sweep = fc10_module("runtime.manufacturing.tuning.sweep")
    tm_sim = fc10_module("runtime.manufacturing.tuning.tm_sim")
    [d3] = [e for e in log.load() if e["decision_id"] == "D3"]
    a, ev = d3["assumptions"], d3["evidence"]["at_budget"]
    groups, budget = a["groups"], a["budget_workload"]
    grid = sweep.default_grid(d3["from_threshold"])
    work, planted = _group_arrays(population, groups)

    names = list(groups)
    best = None
    for t0 in grid:
        for t1 in grid:
            w = _above(work[names[0]], t0) + _above(work[names[1]], t1)
            if w > budget:
                continue
            key = (_above(planted[names[0]], t0) + _above(planted[names[1]], t1), -w, (t0, t1))
            best = key if best is None or key > best else best
    assert best is not None
    assert dict(zip(names, best[2])) == d3["to_thresholds"] == ev["chosen_lines"]
    assert best[0] == ev["chosen"]["in_sample"]["tp"]

    # The best ONE line within the same budget, and both options on the hold-out.
    all_work = np.sort(np.concatenate(list(work.values())))
    all_planted = np.sort(np.concatenate(list(planted.values())))
    single = max((_above(all_planted, t), t) for t in grid if _above(all_work, t) <= budget)
    assert single[0] == ev["single"]["in_sample"]["tp"]
    hold = tm_sim.generate(seed=a["holdout_seed"])
    per_seg = {s: d3["to_thresholds"][g] for g, members in groups.items() for s in members}
    assert _caught(hold, per_seg) == ev["chosen"]["hold_out"]["tp"]
    assert _caught(hold, {s: single[1] for s in tm_sim.SEGMENTS}) == ev["single"]["hold_out"]["tp"]
    assert ev["chosen"]["hold_out"]["tp"] > ev["single"]["hold_out"]["tp"]


# -- week 6: Decision 4, re-derived with pandas --------------------------------

def _payments(population):
    import pandas as pd
    df = pd.DataFrame([(t.customer_id, t.value_date, t.amount) for t in population.transactions],
                      columns=["cid", "date", "amount"])
    df["month"] = df["date"].str[:7]
    df["m"] = df["date"].str[:4].astype(int) * 12 + df["date"].str[5:7].astype(int) - 1
    df["day"] = pd.to_datetime(df["date"]).map(pd.Timestamp.toordinal)
    return df


def _velocity(df, window):
    counts = np.empty(len(df), dtype=int)
    for _cid, idx in df.groupby("cid").indices.items():
        days = df["day"].to_numpy()[idx]
        order = np.argsort(days, kind="stable")
        d = days[order]
        c = np.searchsorted(d, d, side="right") - np.searchsorted(d, d - window, side="right")
        counts[idx[order]] = c
    return counts


def _baseline_ratio(df, months, min_history=5):
    ratio = np.full(len(df), np.nan)
    amt, mon = df["amount"].to_numpy(), df["m"].to_numpy()
    for _cid, idx in df.groupby("cid").indices.items():
        by = {}
        for i in idx:
            by.setdefault(mon[i], []).append(amt[i])
        for i in idx:
            prior = [a for k in range(mon[i] - months, mon[i]) for a in by.get(k, ())]
            if len(prior) >= min_history:
                ratio[i] = amt[i] / np.median(prior)
    return ratio


def _score(df, fires, planted):
    hit = df[fires]
    customers = set(hit["cid"])
    return {"workload": len(set(zip(hit["cid"], hit["month"]))), "caught": customers & planted}


def _refit(df, planted, kind, grid, budget):
    """Exhaustive search, same objective and tie-break as fc-10's fit: most planted
    caught within the budget, then less work, then the LATER grid point."""
    from itertools import product
    keys = sorted(grid)
    feat = (_velocity(df, grid["window_days"][0]) if kind == "amount_and_velocity"
            else _baseline_ratio(df, grid["baseline_months"][0]))
    amt = df["amount"].to_numpy()
    best = None
    for rank, values in enumerate(product(*(grid[k] for k in keys))):
        spec = dict(zip(keys, values))
        if kind == "amount_and_velocity":
            fires = (amt > spec["threshold"]) & (feat >= spec["min_count"])
        else:
            fires = (~np.isnan(feat)) & (amt > spec["floor"]) & (np.nan_to_num(feat) > spec["multiple"])
        s = _score(df, fires, planted)
        if s["workload"] > budget:
            continue
        key = (len(s["caught"]), -s["workload"], rank)
        if best is None or key > best[0]:
            best = (key, {"kind": kind, **spec}, s)
    return best[1], best[2]


def _fires_on(df, spec):
    amt = df["amount"].to_numpy()
    if spec["kind"] == "amount_above":
        return amt > spec["threshold"]
    if spec["kind"] == "amount_and_velocity":
        return (amt > spec["threshold"]) & (_velocity(df, spec["window_days"]) >= spec["min_count"])
    r = _baseline_ratio(df, spec["baseline_months"])
    return (~np.isnan(r)) & (amt > spec["floor"]) & (np.nan_to_num(r) > spec["multiple"])


def test_decision_4_holds_under_an_independent_rebuild(population):
    """D4 advanced the customer-baseline challenger and rejected velocity, on
    numbers fc-10 computed. Rebuild every one here with pandas -- the features,
    the fit, the hold-out, the overlap and the negative control -- and require
    the same answers."""
    from tools.tm_sim_source import fc10_module
    log = fc10_module("runtime.manufacturing.tuning.decision_log")
    ch = fc10_module("runtime.manufacturing.tuning.challengers")
    tm_sim = fc10_module("runtime.manufacturing.tuning.tm_sim")
    [d4] = [e for e in log.load() if e["decision_id"] == "D4"]
    a, ev = d4["assumptions"], d4["evidence"]
    fit_df = _payments(population)
    planted = {c.customer_id for c in population.customers if c.planted}
    hold = tm_sim.generate(seed=a["holdout_seed"])
    hold_df, hold_planted = _payments(hold), {c.customer_id for c in hold.customers if c.planted}

    champ = {"kind": "amount_above", "threshold": d4["from_threshold"]}
    champ_hold = _score(hold_df, _fires_on(hold_df, champ), hold_planted)
    assert len(champ_hold["caught"]) == ev["champion"]["hold_out"]["tp"]
    assert champ_hold["workload"] == ev["champion"]["hold_out"]["workload"]

    for kind in a["kinds"]:
        spec, fitted = _refit(fit_df, planted, kind, ch.GRIDS[kind], a["budget_workload"])
        got = ev["challengers"][kind]
        assert spec == got["spec"], kind
        assert len(fitted["caught"]) == got["in_sample"]["tp"] and fitted["workload"] == got["in_sample"]["workload"], kind
        held = _score(hold_df, _fires_on(hold_df, spec), hold_planted)
        assert len(held["caught"]) == got["hold_out"]["tp"], kind
        o = got["hold_out"]["overlap"]
        assert o["challenger_only"] == len(held["caught"] - champ_hold["caught"]), kind
        assert o["both"] == len(held["caught"] & champ_hold["caught"]), kind

    # The advanced challenger's negative control, rebuilt: labels kept, behaviour removed.
    rs = ev["challengers"]["relative_spike"]
    neg = tm_sim.generate(intensity=0.0)
    neg_df = _payments(neg)
    hit = set(neg_df[_fires_on(neg_df, rs["spec"])]["cid"])
    neg_planted = {c.customer_id for c in neg.customers if c.planted}
    lift = (len(hit & neg_planted) / len(hit)) / (len(neg_planted) / len(neg.customers))
    assert lift == pytest.approx(rs["negative_control"]["lift"], abs=1e-4)
    assert d4["challenger_verdicts"] == {"amount_and_velocity": "REJECT", "relative_spike": "ADVANCE_TO_VALIDATION"}
