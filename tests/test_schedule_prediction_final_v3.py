from __future__ import annotations

import numpy as np
import pytest

from src.ml.schedule_experiment_v3 import choose_threshold, fold_support, lead_time, schedule_rule_probability
from src.ml.temporal_experiment_v2 import RESEARCH_MODE, TARGET_VALIDATION_STATUS, require_research_authorization


def test_prototype_override_is_explicit_and_fail_closed():
    assert TARGET_VALIDATION_STATUS == "MACHINE_PROVISIONAL"
    assert RESEARCH_MODE == "PROTOTYPE_RESEARCH_OVERRIDE"
    require_research_authorization(RESEARCH_MODE)
    with pytest.raises(RuntimeError): require_research_authorization("PENDING")


def test_rule_uses_only_anchor_features():
    assert schedule_rule_probability({"remaining_schedule_months":3,"project_age_months":10,"planned_duration_months":10,"physical_progress":40,"consecutive_stagnant":0}) == .75
    assert schedule_rule_probability({"remaining_schedule_months":20,"project_age_months":2,"planned_duration_months":10,"physical_progress":80,"consecutive_stagnant":0}) == .25


def test_threshold_is_validation_derived_and_capacity_is_separate():
    threshold,capacity=choose_threshold(np.asarray([0,0,1,1]),np.asarray([.1,.2,.7,.9]))
    assert .2 <= threshold <= .9 and capacity != .5


def test_folds_keep_mature_training_outcomes_before_test():
    cohort=[]
    for year in range(2022,2026):
        for month in range(1,13):
            cohort.append({"canonical_project_id":f"P{month}","anchor_month":f"{year}-{month:02d}","event":month%4==0})
    for fold in fold_support(cohort,3):
        if fold["train_rows"]:
            assert fold["latest_training_outcome"] < fold["test_start"]


def test_lead_time_counts_unique_events_without_future_awareness():
    rows=[{"canonical_project_id":"P","anchor_month":"2025-01","event":1,"event_month":"2025-03","probability":.8,"threshold":.5},
          {"canonical_project_id":"P","anchor_month":"2025-02","event":1,"event_month":"2025-03","probability":.7,"threshold":.5}]
    result=lead_time(rows);assert result["event_count"]==1 and result["events_warned"]==1 and result["median_lead_months"]==2
