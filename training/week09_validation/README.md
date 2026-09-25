# Week 9 — validation and governance

**The idea:** a tuning result isn't finished when it looks good. It's finished when someone who didn't build it has tried to break it, when the change can only be applied through a step that refuses surprises, and when the paper that goes to a model-risk committee is generated from the records rather than written from memory.

| | |
|---|---|
| Monday (1 h) | This page |
| Wednesday (1 h) | `week09_exercises.ipynb` |
| Friday (1–2 h) | Built this week in fc-10 (Stage560): `tuning/apply.py` (the governed apply step: a candidate judged by the unchanged detectors against four goldens, refused on any move the decision did not predict, proven on drills with nothing live), five independent challenge memos with point-by-point responses (`data-model/tuning/challenges/`), `tuning/validation.py` (fallbacks, attributable catches, noise alert rate, burn-in, pass marks, warm-up), a "validation" kind of decision evidence, and `tuning/paper.py`, the tuning paper generated from the log |
| Weekend (30 min) | `weekend_note.md` → Decision 7 in fc-10's Tuning Decision Log |

---

## 1. Three lines of defence, in one repository

- **The builder** proposes: the studio, the evidence, the decision log.
- **An independent challenger** tries to break it. This week that meant five reviewer agents, each given read-only access and told to challenge rather than confirm. Every memo is committed with a numbered response to each point.
- **A governed step** applies, or refuses. Nothing reaches the registry except through it.

None of these replaces the others. The builder can't mark their own homework. The challenger can't change the registry. The apply step can't judge whether a change is wise, only whether it does what the decision said it would.

## 2. The apply step: predictions, not permissions

A decision to change a threshold now has to say what the change will move. For each **golden**, the decision records a fingerprint of what that surface should look like once the change is applied. There are four goldens: the TM-SIM backtest, the estate's high-value signals, the money-flow ledger's flags, and the macro queue those signals score into.

The step runs the unchanged detectors against the candidate in a fresh process and refuses if:

- a golden moved that the decision did not predict,
- a predicted golden did not move, or
- a golden moved to a different value than predicted.

Measured on drills: moving £75k to £98k stops five live estate payments alerting and moves E-STONEFIELD from Medium to Low. A decision that predicted only the backtest would be refused, because its author hadn't seen the estate move.

## 3. What the challenges found

Every reviewer's verdict was *stands with conditions*. Nobody said "fine", and nobody said "wrong". Some of what they found:

- **D3:** the segment gain depends on how closely segment tracks customer size in the simulation. Loosen that link and the gain disappears.
- **D4:** 21 of the challenger's 170 hold-out catches fired only on background payments. They were lucky catches, not detections.
- **D5:** the customer-baseline rule's "stable" rating was built into the scenario. A ratio rule can't see a pure multiplication, but a volatility drift moves its workload +63% while the flat line moves +8%.
- **D6:** seven entities tie at the macro cap, not six. The decision quoted the wrong count.
- **D7 (first draft):** the candidate was compared only with the champion, and most of its fallback's extra catches fell in the simulation's first three months.

## 4. A decision re-taken

D7 was drafted, challenged, and **re-taken before it was committed**. The first draft carried the customer-baseline rule with a fallback forward as the candidate. After scoring every rule the log holds, and again after a three-month burn-in, only two rules passed both stated conditions: the champion and D3's two lines alone. D3's lines became the candidate. The spike hybrid stays as the challenger to beat, with more attributable catches but three times the customers and a +55% volatility swing.

The log is append-only, so this could only happen before the commit. After it, the correction would have been a new decision, and D7 would stand in the record as a choice made on incomplete evidence. **Challenge before you commit.**

## 5. The paper writes itself, from the records

`tuning/paper.py` generates Background, Method, Results, Recommendation and Limitations from the decision log, the registry, the apply step's verdict on each decision, and the challenges. Every limitation is a reviewer's point, with its severity and the builder's response. A guard fails if the committed paper falls behind its records.

---

## Check yourself before Wednesday

1. Why is "the tests pass" not the same as "the change does what the decision said"?
2. A reviewer raises five points and the builder accepts all five. Is the decision now sound?
3. Why score every candidate after a burn-in, not only the ones that use a baseline?

<details><summary>Answers</summary>

1. Tests check the code. A prediction checks the consequence. The apply step compares what actually moved against what the decision said would move.
2. Not necessarily. Accepting a point records it; it doesn't fix it. The paper carries every point, so a committee sees what is still open.
3. A comparison is only fair if every rule gets the same treatment. Removing the early months from one rule and not the others would bias the result.

</details>
