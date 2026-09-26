# Week 10 — the capstone engagement

**The brief:** cash deposits over £10k in 30 days, fixed review capacity, a volume reduction expected, and only limited missed risk allowed. Run the whole programme on one new rule, write it up, and publish it.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week10_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): `tuning/cash.py` (a cash-deposit stream over TM-SIM's customers, with planted **structuring**), `tuning/capstone.py` (the engagement: sweep, challenger, an unused hold-out seed, three structuring stresses, drift, a negative control, and the queue worked to capacity), Decision 8 with its independent challenge, and the static export: the tuning paper and a studio snapshot published through a governed publisher with a staleness gate |
| Weekend (30 min) | `weekend_note.md` → your own one-page capstone memo |

---

## 1. The engagement, stated before the work

The owner set the terms first: at least **20% fewer alerts** than the naive £10k line, and at most **5 points of recall** lost against it. Capacity is D2's fixed figure, 522 reviews a year at this sample's scale. Terms written down before the evidence are terms the evidence can fail.

## 2. A scenario that tests the rule, not one that flatters it

Structuring means several deposits kept under a reporting line, in absolute amounts. That's the behaviour the D4 and D7 reviewers asked for: something that isn't relative to the customer's own size.

The first version of the scenario was **degenerate**. Nobody legitimate deposited in the £7k–£10k band, so a near-line rule caught 100 of 100 for 130 reviews. The scenario was widened before any decision, and the module records that it was. **If one rule wins completely, suspect the generator before you celebrate the rule.**

## 3. Stress the line where it is weak

Each rule has its own weak dial:

- **Near-line signature:** structurers who start below the band. It loses 11 points.
- **30-day sum line:** structurers who make fewer deposits. £15k loses 8 points.

A stress test that only moves one rule's weak dial proves nothing about the other. The D8 reviewer found exactly that, and the capstone now runs three stresses.

## 4. At capacity, the order is the rule

When the team can review only part of the alerts, what gets caught depends on the order they work in, not on where the line sits:

- Worked with the most signature hits first, the £15k line's queue catches 90 of 100.
- Worked oldest-first, the **same queue catches 23**.
- The best rule that fits capacity on its own catches 88, and with fewer deposits every plan falls to about 52.

So the engagement can't be met by tuning at this capacity. **D2's staffing gap, now on a second rule, is the finding.**

## 5. Proposed, not changed

There is no cash rule in the registry, so D8 is a **proposal** (`PROPOSE`), not a change. The governed apply step refuses it, because adding a rule kind is a registry change the step won't invent. The paper says the proposed rule runs nowhere today.

## 6. Publish the paper, gate the page

The tuning paper and a studio snapshot are published by a governed publisher that crosses the internal-reference boundary. Its staleness gate compares the committed pages with a **fresh** render, because a new decision makes the paper stale while every hash still agrees with every other.

---

## Check yourself before Wednesday

1. A near-line rule catches everything planted for a tenth of the work. What is the first thing you check?
2. Why is "the line" the wrong question when the team can review only 522 of 4,312 alerts?
3. Why record D8 as `PROPOSE` rather than `CHANGE`?

<details><summary>Answers</summary>

1. Whether the scenario gives the rule its win by construction: its band floor, the count, the spread. Then stress each of those.
2. The team reviews only a slice of the alerts, and the order decides which slice. At capacity, the order is effectively the rule.
3. There's no incumbent to change from. A change from a hypothetical rule would misstate what is running.

</details>
