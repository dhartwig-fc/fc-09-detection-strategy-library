# Week 8 — risk scores and calibration

**The idea:** a rule says yes or no. A score puts every case in order, and the team works down the order until the day runs out. That changes what "tuning" means. You're no longer choosing a line; you're choosing an ordering, and then asking what a place in that order actually means.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week08_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): `tuning/macro_preview.py` (a candidate macro-triage config run through the REAL scorer, band moves, cap saturation, queue movement), `tuning/calibration.py` (the champion and Decision 4's customer-baseline rule as one ranked score, worked to the D2 budget, with bands, a hold-out, a cap sweep and a weight sweep), a "calibration" kind of decision evidence, `GET /api/calibration`, `GET /api/macro`, and two studio panels |
| Weekend (30 min) | `weekend_note.md` → Decision 6 in fc-10's Tuning Decision Log |

---

## 1. Rules, scores and queues

- **Rule:** fires or doesn't. Workload is whatever the rule produces.
- **Score:** every case gets a number. Workload is whatever the team **chooses** to work: the top N.

With a score, the budget is fixed first and the score decides who fills it.
This week's score blends the two rules the log already holds: the champion
(largest payment against £75k) and Decision 4's customer-baseline rule
(largest multiple of the customer's own three-month median against 4×).

## 2. Ranking is not calibration

Two different questions:

- **Ranking:** is a higher score a likelier case? Cut the ordered list into bands and check that the planted rate falls as you go down.
- **Calibration:** does a score of X mean the same rate everywhere? Take the score **edges** from one population and apply them to another the score never saw.

This week's score passes the first test on the hold-out: no band is out of
order. It fails the second at the very top. The top 0.5% band is 46% planted
where it was built, and 35% at the same score edge on the hold-out. The order
transfers; the number doesn't. **Never read a score as a probability** unless
it has been calibrated on outcomes and checked out of sample.

## 3. Why the bands are uneven

Ten equal deciles would put almost every planted month in the first tenth and
compare noise across the other nine. The budget is the top 4% of months, so
the bands are finest at the top (0.5%, 1%, 2%, 4% … 32%, rest), where the work
is.

## 4. The cap, and the tie-break under it

A cap flattens every score above it to the same number. Something then has to
order the tie. The live queue does it alphabetically, which is blind to risk.

- While the team can work **every** tied case, the cap costs nothing: all of them are worked.
- Once the tie is **bigger than capacity**, the tie-break decides who gets reviewed.

Measured this week: a cap of 100 ties 1,652 months against a budget of 2,419,
so it's free. A cap of 75 ties 3,375, and recall falls from 166 to 112, back
to the plain champion's. **The cost of a cap is that drop.** The missed cases
weren't lost: they were in the tie, where a tie-break that could see the
answers would have found 165 of them, and the alphabetical order didn't reach
them. You can only measure that where labels exist.

The estate's macro score has a cap of 100, and 6 of its 48 entities sit on it
today. It has three dispositioned cases, so this can't be measured there. The
monitoring rule follows: watch the size of the tie against the capacity that
works it.

## 5. Weights you can't fit

The estate can't fit its macro weights: three labelled outcomes is not a
training set. What it **can** do is show what a proposed change does before
anyone governs it: which entities change band, what saturates, and who moves
in the queue. That's the preview. It tells you what a change does, not
whether the change is right.

On TM-SIM, where labels exist, the weights turn out not to matter much: any
amount weight from 20 to 60 catches between 161 and 168. When the answer
barely moves across the sensible range, the weights aren't the decision.

---

## Check yourself before Wednesday

1. A score ranks perfectly on a hold-out but its top band's rate is ten points lower there. Is it calibrated?
2. Why is a cap harmless for one team and costly for another, on the same scores?
3. Your score, worked to the budget, catches 5 more than the best rule alone and nothing neither rule catches. What have you learned?

<details><summary>Answers</summary>

1. It ranks well but it isn't calibrated. The ordering holds; the score-to-rate mapping doesn't.
2. It depends on capacity. The cap is free while the team works every tied case, and costly once the tie is bigger than what the team can work.
3. The score mostly re-orders cases the rules already find. It's a small gain in which cases get worked first, not new coverage, and it has to beat the cost of governing a model.

</details>
