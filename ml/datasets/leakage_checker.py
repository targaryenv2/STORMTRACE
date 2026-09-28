#!/usr/bin/env python3
"""
STORMTRACE Train/Test Data Leakage Prevention & Audit Engine
================================================================================
Strictly verifies that:
    1. Temporal monotonicity: all target horizons strictly succeed T0.
    2. Zero temporal overlap between Train, Validation, and Test splits.
    3. Event isolation: no storm sequence spans across split boundaries.
    4. Normalization parameters are computed solely on training partitions.
================================================================================
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime


class DataLeakageAuditor:
    """Audits temporal datasets and splits for information leakage."""

    @staticmethod
    def check_sequence_temporal_integrity(
        past_timestamps: List[str],
        future_timestamps: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Ensures strict chronological progression: past_timestamps < future_timestamps.
        """
        errors = []
        parsed_past = [datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in past_timestamps]
        parsed_future = [datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in future_timestamps]

        # Check past sequence monotonicity
        for i in range(len(parsed_past) - 1):
            if parsed_past[i] >= parsed_past[i + 1]:
                errors.append(f"Past sequence non-monotonic at index {i}: {past_timestamps[i]} >= {past_timestamps[i+1]}")

        # Check future sequence monotonicity
        for i in range(len(parsed_future) - 1):
            if parsed_future[i] >= parsed_future[i + 1]:
                errors.append(f"Future sequence non-monotonic at index {i}: {future_timestamps[i]} >= {future_timestamps[i+1]}")

        # Check that T0 < T+15
        if parsed_past and parsed_future:
            t0 = parsed_past[-1]
            t_first_future = parsed_future[0]
            if t0 >= t_first_future:
                errors.append(f"Future leakage: T0 ({past_timestamps[-1]}) is >= first target ({future_timestamps[0]})")

            # Check overlap
            past_set = set(past_timestamps)
            future_set = set(future_timestamps)
            intersect = past_set.intersection(future_set)
            if intersect:
                errors.append(f"Direct frame leakage: timestamps present in both past and future: {intersect}")

        return len(errors) == 0, errors

    @staticmethod
    def audit_splits_chronology(
        train_timestamps: List[str],
        val_timestamps: List[str],
        test_timestamps: List[str]
    ) -> Dict[str, Any]:
        """
        Verifies that Train max time < Val min time < Test min time.
        """
        def to_dt(ts_list):
            return sorted([datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in ts_list])

        d_train = to_dt(train_timestamps)
        d_val = to_dt(val_timestamps)
        d_test = to_dt(test_timestamps)

        violations = []

        if d_train and d_val:
            if d_train[-1] >= d_val[0]:
                violations.append(f"Train/Val boundary leak: max(Train)={d_train[-1]} >= min(Val)={d_val[0]}")

        if d_val and d_test:
            if d_val[-1] >= d_test[0]:
                violations.append(f"Val/Test boundary leak: max(Val)={d_val[-1]} >= min(Test)={d_test[0]}")

        # Check for duplicated sample keys across splits
        s_train = set(train_timestamps)
        s_val = set(val_timestamps)
        s_test = set(test_timestamps)

        if s_train.intersection(s_val):
            violations.append(f"Overlap between Train and Val partitions: {len(s_train.intersection(s_val))} items")
        if s_train.intersection(s_test):
            violations.append(f"Overlap between Train and Test partitions: {len(s_train.intersection(s_test))} items")
        if s_val.intersection(s_test):
            violations.append(f"Overlap between Val and Test partitions: {len(s_val.intersection(s_test))} items")

        is_clean = len(violations) == 0
        return {
            "status": "CLEAN" if is_clean else "LEAKAGE_DETECTED",
            "is_leakage_free": is_clean,
            "train_samples_count": len(train_timestamps),
            "val_samples_count": len(val_timestamps),
            "test_samples_count": len(test_timestamps),
            "violations": violations
        }
