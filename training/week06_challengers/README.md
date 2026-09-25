# Week 6 — challenger rules

**The idea:** a live rule is replaced on evidence, not argument. Run an alternative beside it, at the same workload, and see who each catches that the other misses.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week06_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): `tuning/challengers.py` (the champion, two challengers, a fit within the champion's workload, hold-out scoring, overlap, a negative control, the cold start, and an explanation for every alert), a "challenger" kind of decision evidence, `GET /api/challengers`, and a champion & challenger panel on the studio page |
| Weekend (30 min) | `weekend_note.md` → Decision 4 in fc-10's Tuning Decision Log |

---

## 1. Champion and challenger

The **champion** is the rule that runs: `high_value` at £75,000. A
**challenger** is an alternative that is scored beside it and never touches a
live alert. That separation is the whole method. A challenger can be as
experimental as you like because it can't affect a customer until it has
earned it.

## 2. Two challengers, and what each is aimed at

- **Amount and velocity** (the curriculum's): a large payment *and* several payments in a short window. It's aimed at bursts: structuring, mule activity, rapid movement.
- **Customer baseline** (the one Decisions 1–3 each asked for): a payment more than *k* times the customer's own recent median. It's aimed at a change in behaviour, whatever the customer's size.

A challenger aimed at behaviour that isn't in the data will lose, and that
tells you something about the data rather than about the rule. Week 6 shows
exactly that.

## 3. Compare at the same workload

The same rule as week 5: a challenger that catches more by making more work
has proved nothing. Each challenger is fitted **within the champion's
workload** (customer-months), then scored on a **hold-out**. The fair yield
figure is **caught per 100 reviews**, because one rule may alert a large
customer every month while another alerts many customers once.

## 4. Overlap

Totals hide the useful part. For each challenger, count four groups of planted
customers: **both** rules catch them, **only the champion** does, **only the
challenger** does, **neither** does. A challenger that catches only what the
champion already catches adds nothing, however good its numbers look.

## 5. Two honesty checks

- **Negative control.** Keep the labels and remove the planted behaviour. A rule that still "catches" the planted customers is reading something other than the behaviour. Lift near 1 is what you want to see.
- **Construction bias.** The customer-baseline rule mirrors how the planted spike was generated. Planted truth favours it by construction, so a win here shows it *can* catch what was planted. It doesn't show it beats the champion on real behaviour. That's why Decision 4 advances it to validation rather than adopting it.

## 6. Explainability

An alert nobody can explain is not an alert anyone should act on. Each
challenger alert explains itself in the rule's own terms, for example *"payment
48,210 is 6.3x this customer's baseline (median of the previous 3 months)"*.
A composite score that can't do that is harder to defend to an examiner.

---

## Check yourself before Wednesday

1. A challenger catches 88 planted customers and the champion 122, and all 88 are among the champion's 122. Is it worth keeping?
2. Why is "caught per 100 reviews" fairer than precision here?
3. The baseline rule wins on planted truth. Name two reasons that isn't enough to switch the live rule.

<details><summary>Answers</summary>

1. No. It catches nothing the champion misses, so it adds work and no coverage.
2. Precision here is per alerted customer, and the two rules alert on very different numbers of customers for similar work. Per 100 reviews measures catches against the unit the team actually works.
3. Planted truth favours it by construction; it alerts far more distinct customers; and it can't see customers who spike before they have a baseline. Any one of these would do.

</details>
