# Week 1 — the tuning framework

**The idea:** decide how success will be measured before touching a threshold.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week01_exercises.ipynb` |
| Friday (1–2 h) | Built already for this week: fc-10 `tuning/tm_sim.py`, `tuning/metrics.py` and their guards (Stage560) — read them against this page |
| Weekend (30 min) | `weekend_note.md` |

---

## 1. The four outcomes of an alert

Every customer, for one rule over one period, lands in exactly one box:

| | Truly suspicious | Not suspicious |
|---|---|---|
| **Alerted** | True positive (TP) — the rule did its job | False positive (FP) — an investigator's time spent on nothing |
| **Not alerted** | False negative (FN) — **missed risk**, the regulatory exposure | True negative (TN) — correctly left alone |

Everything in tuning is a trade between the FP box (cost) and the FN box (risk).

## 2. The rates, and what each one answers

| Rate | Formula | Question it answers |
|---|---|---|
| Precision | TP / (TP + FP) | Of the alerts we raise, how many are worth raising? (alert **yield**) |
| Recall | TP / (TP + FN) | Of the real cases, how many do we catch? (**coverage**) |
| FPR | FP / (FP + TN) | Of the innocent population, how much do we disturb? |
| F1 | harmonic mean of P and R | One number when P and R must both be decent — use with care |
| Lift | precision / prevalence | How much better than picking customers at random? 1.0 = the rule knows nothing |

## 3. Why accuracy fails in AML

Accuracy is (TP + TN) / everyone. When 4% of customers are suspicious, a rule
that **alerts on nobody** is 96% accurate and catches nothing. Because true
cases are rare, accuracy is dominated by the TN box, which is the one box
nobody is paying to get right. In this week's notebook the do-nothing rule
beats the real rule on accuracy. Keep that result in mind whenever someone
reports one number.

## 4. SAR-based labels versus proxy labels

A backtest needs to know which alerts were right. Where do the labels come from?

- **SAR / disposition outcomes.** These are the real thing, but they're rare, slow to arrive, and **biased by the current rules**: you only learn outcomes for customers the rules already alerted on. A customer the rule never flagged has no outcome at all, so recall against these labels is structurally flattering.
- **Proxy labels.** These are escalations, case openings, or expert-labelled samples. They arrive faster and in greater volume, but they carry the same selection bias plus the noise of the proxy.
- **Planted truth (what NEXUS uses now).** A synthetic population where the behaviour was put there on purpose. Every miss is visible, which makes it ideal for stress-testing and learning. It is **not** evidence of real-world performance and must never be presented as a SAR outcome.

The NEXUS estate today holds 3 dispositioned cases. That is why the studio
starts on planted truth, and why `model_performance_mi` refuses to report a
conversion rate until it has enough labels.

## 5. Capacity is a constraint, not an afterthought

The statistically best threshold can be operationally impossible. Twelve
investigators each working 25 alerts a day is **300 alerts/day**. A threshold
producing 560 a day either creates a backlog (SLA breaches, stale alerts) or
gets worked badly. Week 4 turns this into the capacity frontier, and every
decision from week 3 onward states its alert volume.

## 6. The rule lifecycle

Design → implement → **backtest** → tune → approve → deploy → monitor → re-tune.
Each tuning step leaves evidence: what was tested, what moved, what was
assumed, and who decided. That evidence trail is the Tuning Decision Log, and
it is what model validation and audit ask for.

---

## Governance reading (public sources, read the relevant sections)

- **US Federal Reserve / OCC SR 11-7**, *Guidance on Model Risk Management*: conceptual soundness, ongoing monitoring, outcomes analysis. TM rules and thresholds are treated as models under it.
- **UK PRA SS1/23**, *Model risk management principles for banks*: the UK equivalent. Read the principles on model identification and validation.
- **The Wolfsberg Group** statement on effective monitoring for suspicious activity: argues for measuring **effectiveness** over alert volume. It is the policy backdrop to this whole programme.
- **FFIEC BSA/AML Examination Manual**, the suspicious activity monitoring section: what an examiner expects a monitoring system's tuning to evidence.

---

## Check yourself before Wednesday

1. A rule raises 400 alerts, 20 of them true, and there were 50 true cases in total. What are its precision and recall?
2. Why can't recall be measured from SAR outcomes alone?
3. What would lift of 1.0 tell you about a rule?

<details><summary>Answers</summary>

1. Precision 20/400 = 5%; recall 20/50 = 40%.
2. Customers the rules never alerted on never get an outcome, so the missed cases (the FN box) are invisible.
3. The rule is no better than picking customers at random: the label and the rule's behaviour are unrelated.

</details>
