# Week 7 — stability and drift

**The idea:** a rule that works this year may fail next year. Test the rule you'd keep against the years you haven't seen yet.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week07_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): `tuning/drift.py` (a stated drift scenario over three periods, every rule held fixed, workload/recall/yield per period, a monthly transient check, KS and PSI written by hand), a "drift" kind of decision evidence, `GET /api/drift`, and a stability panel on the studio page |
| Weekend (30 min) | `weekend_note.md` → Decision 5 in fc-10's Tuning Decision Log |

---

## 1. Four ways a population moves

- **Inflation / growth:** everyone pays a bit more each year.
- **Behaviour change:** one kind of customer steps up, e.g. a segment's business grows.
- **Data drift:** the feed changes: a new product, a new channel, a field that means something new.
- **Seasonality:** the same customers behave differently at different times of year.

This week's scenario is the first two, stated as assumptions: 10% a year
inflation, and business, corporate and correspondent payments stepping up
1.6× from month 7 of the second year.

## 2. Hold the rule fixed

The test is simple: take each rule **as tuned** and run it, unchanged, over
each later period. Re-tuning every year hides the problem, because the
question is what happens *between* tunings.

## 3. KS and PSI

- **KS (Kolmogorov–Smirnov):** the largest gap between two cumulative distributions. From 0 (identical) to 1 (no overlap).
- **PSI (Population Stability Index):** cut the old distribution into ten equal slices and compare how the new one fills them. By convention, under 0.1 is stable, 0.1–0.25 is a moderate shift, and over 0.25 is significant.

Both are standard, and both describe the **whole** distribution.

## 4. Why they miss what matters to a threshold rule

A threshold rule lives in the **tail**: the few payments above its line. A shift
that barely moves the bulk of payments can move the tail a lot. This week that
happens exactly: PSI on payment amounts stays at or below 0.06 ("stable") in
every period, while the £75k line's workload more than doubles.

The lesson for monitoring: **watch each rule's own alert volume**, not only
the inputs. It's the rule's output that the team has to work.

## 5. Indexing, and why the obvious index is the wrong one

The obvious fix for inflation is to scale the threshold by it. Measured this
week: indexing £75k to the **median** payment only halves the drift. The median
is dominated by retail customers, while the step change hit the non-retail
customers who make the tail. A threshold needs an index built from the tail,
or one per segment.

## 6. Transients

An annual total can look fine while one quarter floods the queue. The
customer-baseline rule is a ratio to each customer's own spend, so it is blind
to plain inflation. But when a whole segment's business steps up, every
customer in it looks like a spike until their baseline catches up. That's a
bump of about a quarter, the length of the baseline window. Monitoring
monthly, not annually, is what catches it.

---

## Check yourself before Wednesday

1. PSI is 0.04 and the rule's workload rose 70%. Is the population stable?
2. Why does a rule that compares a payment with the customer's own median ignore inflation?
3. What would you monitor, and how often, to catch next year's drift early?

<details><summary>Answers</summary>

1. The bulk of payments is stable, but the tail isn't, and the tail is what the rule works on. For this rule, the population has drifted.
2. Inflation scales the payment and the customer's median by the same factor, so their ratio doesn't change.
3. Each rule's own alert volume, monthly, against a baseline period, with stated tolerances. Keep PSI and KS as supporting signals, not the trigger.

</details>
