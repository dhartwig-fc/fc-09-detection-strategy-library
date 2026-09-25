# Week 5 — segment calibration

**The idea:** one threshold rarely fits every kind of customer, but each extra line is a line someone has to justify, monitor and defend.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week05_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): customer **segments** in TM-SIM, `tuning/segments.py` (per-segment curves, an exact fit within a workload budget, a **hold-out** comparison, line groups), a "segments" kind of decision evidence, `GET /api/segments`, and a segments panel on the studio page |
| Weekend (30 min) | `weekend_note.md` → Decision 3 in fc-10's Tuning Decision Log |

---

## 1. Why one line is wrong for everyone

The `high_value` blind spot from week 1 is a segment problem in disguise. A
£30,000 payment is a fifteen-fold spike for a retail customer and a routine
Tuesday for a corporate one. A single line has to sit somewhere, and wherever
it sits it is too high for one population and too low for another. So it
misses the small customers' spikes while flooding the queue with the large
customers' routine business.

TM-SIM now gives every customer a KYC type: **retail, business, corporate or
correspondent**. The type is drawn loosely tied to the customer's payment
scale, the way it is in a real book: related to size, but not a proxy for it.

## 2. Segment options

A segment is anything you can defend drawing a line along:

- **customer type:** retail vs business vs corporate vs correspondent (this week);
- **geography:** domestic vs high-risk corridors;
- **product:** current account vs trade finance vs correspondent nostro;
- **peer group:** customers of similar size and activity, often the best fit and the hardest to govern.

## 3. Compare at the SAME budget

A segmented rule is only better if it catches more **for the same work**. The
fit this week holds the workload fixed (D2's 2,419 customer-months a year) and
asks which lines catch the most planted customers inside it. Comparing a
segmented rule that makes twice the work with a single line that doesn't
proves nothing.

## 4. Overfitting, and why the hold-out is the answer

Fit four lines to one population and they will be better on **that**
population, partly by memorising its accidents. The honest test is a
**hold-out**: a second population drawn the same way with a different seed,
where the lines were not fitted. The gain that survives on the hold-out is
real; the rest was fit to noise. Every comparison this week reports both.

## 5. Thin segments

A line fitted to a handful of true cases is decided by those cases. This week's
floor is **10 planted customers per line**. Below it the line is flagged
**thin**: not refused, but not trusted. Corporate has 9 planted and
correspondent 1, so their own lines are thin. Measured across five fresh
populations, the corporate line swings by £65k and the correspondent line
never leaves the top of the grid: the fit has switched it off. Grouping them with business
into one "non-retail" line gives a line resting on 44.

## 6. Complexity has a cost

Each line is a threshold to document, validate, monitor for drift (week 7) and
explain to an examiner. The curriculum's success criterion is the right one:
*explain the improvement achieved without creating unjustified complexity.*
The studio's segments panel shows each option's gain and cost in the same row.

---

## Check yourself before Wednesday

1. Four lines catch 155 in-sample and 154 on the hold-out; two lines catch 151 and 149. Which do you recommend, and why?
2. Why must the segmented and single-line options be compared at the same workload?
3. A line is fitted on 1 planted customer. What will happen to it on the next population?

<details><summary>Answers</summary>

1. Two lines. Four buy 5 more catches on the hold-out, but two of the four lines rest on 9 and 1 planted cases, which is too few to trust or defend. Two lines keep nearly all the gain with none thin.
2. Otherwise you're comparing a rule that does more work with one that does less. More catches from more work isn't a better rule, just a bigger queue.
3. Either it moves, set wherever that customer's payments fall, or, as the notebook shows for correspondent, the fit pushes it to the top of the grid on every population. That switches the line off: it catches no one and still has to be governed. Neither outcome is a line you can defend.

</details>
