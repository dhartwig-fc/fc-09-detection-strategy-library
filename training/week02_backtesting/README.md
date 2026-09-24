# Week 2 — backtesting fundamentals

**The idea:** evaluate a rule's performance on history before anyone proposes to change it.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week02_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): the governed **TM rule registry**, both hardcoded `75000`s lifted into it, and `tuning/backtest.py` with the committed **baseline** |
| Weekend (30 min) | `weekend_note.md` |

---

## 1. What a backtest is, and the one rule that makes it honest

A backtest replays a rule over a period whose outcomes are known and counts
what it would have done: the alerts it raises, how many were right, and what
it missed. The honest version has one rule above all: **backtest the rule that
actually runs.** A threshold copied into a notebook is a second copy of the
rule, and the two drift apart.

This is why Week 2's build moved `high_value` into a governed registry before
building the backtest. Detection (`daily_run/detect.py`), the case ledger
(`fusion/money_flow.py`) and the studio's backtest now read the **same
value from the same file**. Before this week the value was written out twice.

## 2. Alert yield and coverage

These are the two numbers an operations lead actually asks for:

- **Yield (precision).** Of the alerts we work, how many are worth working? Low yield means investigator time spent on noise.
- **Coverage (recall).** Of the behaviour we're meant to catch, how much do we catch? Low coverage is regulatory exposure, and it's the one you can't see from the queue.

The backtest reports coverage **per planted scenario** as well as overall.
With one scenario the two are equal. When the population carries several, an
average can hide a rule that catches one behaviour well and another not at
all.

## 3. Retrospective testing: what "history" means here

In a bank, history is past transactions plus past dispositions. At NEXUS today
it's **TM-SIM**: a year of synthetic payments where the suspicious behaviour
was planted on purpose. That is a stress test of the rule, not evidence about
the real world, and the baseline file says so in its own body
(`"label_source": "PLANTED_TRUTH"`).

## 4. Selection bias: the trap in real backtests

Real outcome labels exist only where somebody looked, and people only look
where a rule alerted. So a backtest against SAR outcomes:

- knows the precision of the alerts it raised, **and**
- knows **nothing** about the customers it never raised,

and therefore reports recall as if every true case had been alerted. This
week's notebook computes the "SAR-only" recall of `high_value` next to its
true recall on the planted population. The gap between the two is the bias.

## 5. Sample design: measuring what the rule missed

The fix for selection bias is to **look where the rule didn't**: review a
random sample of non-alerted customers (a below-the-line sample), count the
true cases in it, and scale up. Two design questions decide whether that
estimate means anything:

- **How big a sample?** The false-negative rate is small, so a small sample can easily find zero and "prove" nothing is missed. The notebook shows the confidence interval shrinking as the sample grows.
- **Random, or stratified?** Sampling just below the threshold finds more misses per review hour, but it estimates only that band. A random sample estimates the whole population. Say which one you used.

---

## Check yourself before Wednesday

1. A rule raised 400 alerts, and 40 were SARs. Nobody reviewed the 9,600 customers it didn't alert. What can you say about its recall?
2. You review a random 200 of those 9,600 and find 2 true cases. Roughly how many did the rule miss?
3. Why must the backtest read the same threshold as detection, rather than a copy?

<details><summary>Answers</summary>

1. Nothing yet. Precision is 10%, but recall needs the misses, and they were never looked at.
2. About 1% of 9,600 ≈ 96 missed, with a wide interval (Wednesday computes it). That puts recall near 40 / (40 + 96) ≈ 29%, not the 100% a SAR-only view implies.
3. A copy drifts. The tuned value would be applied in one place and backtested in another, and the evidence would describe a rule that doesn't run.

</details>
