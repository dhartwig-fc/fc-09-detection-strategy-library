# Week 4 — alert volume and capacity

**The idea:** a rule's recall only counts if somebody reviews the alerts, so capacity is part of the rule.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week04_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): `tuning/capacity.py` (arrivals, a working-day queue, the capacity frontier, **effective recall**), `GET /api/capacity`, and a capacity panel on the studio page |
| Weekend (30 min) | `weekend_note.md` → Decision 2 in fc-10's Tuning Decision Log |

---

## 1. Volume is not capacity

A threshold's alert count is how much work it makes. Capacity is how much work a
team can do. The two meet in a **queue**: alerts arrive every calendar day,
investigators work weekdays, and anything not worked waits. A backlog isn't a
paperwork problem. An alert still in the queue has caught nothing yet, and one
worked months late is often too late to matter.

## 2. The unit of work

Before you can compare volume with capacity you must say what "one alert" is. Three
honest answers give three different workloads for the same rule:

- **once per customer per year:** understates the work, and bunches it all at the
  start of the window (every large customer alerts "for the first time" in month one);
- **once per customer per month (a 30-day dedupe):** how most TM queues work, and
  it counts the repeat reviews a flat threshold forces on big legitimate customers;
- **every alerting payment:** the upper bound, with no dedupe at all.

The studio uses the customer-month. That was the owner's call, made after
measuring all three: the choice moved the capacity-feasible threshold from £95k
to £177.5k.

## 3. Scale: a sample is not a bank

TM-SIM has 5,000 customers. A capacity like "300 reviews a day" belongs to a bank's
whole book, so it needs a stated scale before it means anything here. The studio
reads TM-SIM as a **1-in-150 sample** (a 750,000-customer book), so 300 a day at
bank scale becomes 2.0 per working day in the sample. That factor is an
assumption, and Decision 2 records it as one.

## 4. The queue, and Little's law

Over a long run, **backlog ≈ arrival rate × average wait**. If alerts arrive faster
than they're worked, the backlog and the wait both grow without limit, and no
threshold short of the one that fits will stop it. Even when the yearly volume
fits, arrivals are uneven, so a line that fits on paper can still end the year
behind. The notebook shows both.

Two rules make the model honest rather than flattering:

- **Idle capacity is not banked.** A quiet Tuesday doesn't buy extra reviews for
  next week's peak.
- **A weekend alert counts as received on Monday.** Waits are measured from the
  first day it could have been worked.

## 5. Effective recall

**Effective recall** is the share of true cases whose alert was actually *worked*,
within the year or within an SLA. It's the number that matters once capacity is
real, and it can turn the usual intuition upside down:

| At 2.0 reviews / working day | Alerted recall | Effective recall | Within 10 working days |
|---|---|---|---|
| £75,000 (today) | 0.550 | 0.135 | 0.000 |
| £177,500 (capacity frontier) | 0.325 | 0.325 | 0.325 |

A higher line that the team can keep up with catches **more** than a lower line
that drowns the queue.

## 6. Staffing is a decision too

When the line you want doesn't fit, there are only three moves: raise the line,
raise capacity, or change the rule. Decision 2 (2026-09-25) chose to hold £75,000
and name the capacity gap: about **1,390 reviews a day at bank scale**, 4.6× the
stated team. That makes it a staffing ask, outside tuning, and until it's met the
drowned queue is the known state. The week-6 challenger may change how much work
the line makes.

## Reading (model governance)

- Supervisory expectations on alert backlogs: an unworked alert is a control
  failure, not a tuning statistic. Find out what your own institution's SLA for
  first review is, and who is told when it's breached.
- Queueing basics: Little's law, and why utilisation near 100% makes waits explode.
