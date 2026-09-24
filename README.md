# fc-09-detection-strategy-library

Detection strategy for the NEXUS platform: how transaction-monitoring rules are
measured, tuned and evidenced.

It currently holds the **TM tuning training programme**, ten weeks run alongside
the fc-10 Tuning Studio build (Stage560). The studio lives in fc-10 and stays
free of scientific-Python dependencies. This repository is where scikit-learn,
scipy, seaborn and Jupyter are allowed, and fc-10 never imports from here.

| Path | Holds |
|---|---|
| `training/` | The weekly programme: Monday reading, Wednesday notebook, weekend note |
| `tools/tm_sim_source.py` | Reaches fc-10's TM-SIM generator and metrics. Nothing is copied |
| `tests/test_parity_with_fc10.py` | The oracle: fc-10's hand-written metrics must agree with scikit-learn on the same population |

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export FC10_REPOSITORY=~/nexus-code/.worktrees/tuning-studio
.venv/bin/python -m pytest
```

All data is SYNTHETIC_DEMONSTRATION_DATA. Every rate is against planted truth,
not SAR outcomes.
