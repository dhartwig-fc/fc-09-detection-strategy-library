"""Reach fc-10's TM-SIM generator and metrics from the training workspace.

fc-10 owns the population and the studio's metrics; this repository owns the
learning. Nothing is copied across -- a copied generator would drift from the
one the studio measures, and the training would stop checking the build.

The fc-10 checkout is named, never guessed: FC10_REPOSITORY must point at it
(the repository root, or its nested fc-10-intelligence-repository-layer/). The
same override convention fc-10 uses for its own siblings -- where two checkouts
exist, guessing is how the wrong one gets measured.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ENV = "FC10_REPOSITORY"
_NESTED = "fc-10-intelligence-repository-layer"
_MODULE = Path("runtime/manufacturing/tuning/tm_sim.py")


def fc10_platform() -> Path:
    """The nested fc-10 platform directory that holds runtime/manufacturing/."""
    raw = os.environ.get(ENV)
    if not raw:
        raise RuntimeError(
            f"{ENV} is not set. Point it at the fc-10 checkout that carries the "
            f"tuning package, e.g.\n  export {ENV}=~/nexus-code/.worktrees/tuning-studio")
    root = Path(raw).expanduser().resolve()
    for candidate in (root / _NESTED, root):
        if (candidate / _MODULE).is_file():
            return candidate
    raise RuntimeError(f"{ENV}={root} has no {_MODULE} (checked {root / _NESTED} and {root})")


def load():
    """Import fc-10's (tm_sim, metrics) modules from the named checkout."""
    platform = str(fc10_platform())
    if platform not in sys.path:
        sys.path.insert(0, platform)
    tm_sim = importlib.import_module("runtime.manufacturing.tuning.tm_sim")
    metrics = importlib.import_module("runtime.manufacturing.tuning.metrics")
    return tm_sim, metrics


def population_frames(**kwargs):
    """(transactions, customers, population) for the notebooks."""
    import pandas as pd

    tm_sim, _ = load()
    pop = tm_sim.generate(**kwargs)
    txns = pd.DataFrame([t.__dict__ for t in pop.transactions])
    customers = pd.DataFrame([c.__dict__ for c in pop.customers])
    customers["max_amount"] = customers["customer_id"].map(pop.max_amount_by_customer())
    return txns, customers, pop
