# Week 3 — threshold optimisation

**The idea:** a threshold is chosen from a curve, not argued from one point, and the curve cannot choose it for you.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week03_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): `tuning/sweep.py`, **studio v0** (`tuning_service.py`, `GET /api/sweep` and a page with the curve), and a read-only guard that hashes `data-model/` around every route |
| Weekend (30 min) | `weekend_note.md` → the first entry in fc-10's **Tuning Decision Log** (D1) |

---

## 1. A sweep, and what it can and cannot tell you

A sweep runs the same rule at every threshold on a grid and records what it
would have done at each: alerts, TP, FP, FN, precision, recall. Plotted
against the threshold, it shows the whole trade at once:

- raising the threshold can only **remove** alerts, so alert volume and recall
  fall monotonically;
- precision usually rises as the line moves up, because the surviving alerts
  are the more extreme ones — but it is not guaranteed to, and at the far end
  it becomes **undefined** when nothing alerts at all.

What a sweep cannot do is pick a point. Every point on it is a different
answer to the question "what is a missed case worth, next to a wasted
alert?", and the curve doesn't know the answer.

## 2. Sensitivity: where the curve is steep

Around today's threshold, how much recall does each £10k buy or cost? Where the
curve is steep, a small move changes a lot, so the choice needs strong
evidence. Where it's flat, the choice barely matters, and arguing over it is
wasted effort. Measure the slope before debating the point.

## 3. The precision/recall trade-off, and why max-F1 is not a decision

F1 is the harmonic mean of precision and recall. Its maximum is a real point
on the curve, but choosing it means **assuming** misses and false alerts
matter in a particular fixed proportion — one that nobody in the business
agreed to. On TM-SIM, max-F1 sits at £187,500 and catches under a third of
planted cases. Quote it as a landmark, never as a recommendation.

## 4. Cost-weighted optimisation

State the assumption out loud: one missed case costs as much as *k* false
alerts. Then the best threshold minimises `k·FN + FP`. Scan *k* and the
optimum moves as a **staircase**: the dearer a miss, the lower the line. The
studio's `cost_optimal_ranges` does this scan over FN:FP 1–100.

Two things follow:

- **The ratio is the decision.** Once *k* is agreed, the threshold follows
  mechanically. The work is agreeing *k*, and writing down who agreed it.
- **A threshold can be dominated.** If today's line isn't the optimum for
  *any* plausible *k*, then whatever a miss is worth, something else costs
  less. That is exactly what the sweep found for `high_value` at £75,000.

## 5. Planted truth is a stress test, not a verdict

Every rate here is against labels the generator planted. That makes the sweep
excellent at showing a rule's **shape**: the value-spike scenario is relative
to each customer's own baseline, so no flat amount line catches it well, and
the curve shows that plainly. It makes the sweep a poor basis for **moving a
live threshold**, because the best point depends on how we chose to plant
the behaviour. The notebook's last exercise turns the scenario's intensity
down and watches the optimum move.

## 6. What Decision 1 recorded

D1 (2026-09-24) held `high_value` at £75,000. The evidence: it's dominated on
planted truth and max-F1 is poor. Holding was the decision because a move is a
call on *k* nobody has made, on a population whose truth we planted. It is
revisited under a capacity limit (Decision 2, week 4) and against a relative,
customer-baseline challenger (Decision 4, week 6). The entry lives in fc-10's
`data-model/tuning/decision_log.jsonl`. A test recomputes its evidence on every
run, and this repository's parity test re-derives the dominance claim in numpy.

## Reading (model governance)

- Supervisory guidance on model risk (SR 11-7): *outcomes analysis* and
  *sensitivity analysis* — what the regulator means by testing a threshold,
  and why assumptions must be documented as assumptions.
- Your own institution's alert-tuning procedure, if you have one: find the
  place where the cost of a missed case is written down. Usually it isn't.
