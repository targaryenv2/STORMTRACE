#!/usr/bin/env python3
"""
STORMTRACE Meteorological Verification & Skill Score Metrics Engine
================================================================================
Calculates standard meteorological forecast verification scores from dynamic
prediction grids vs future ground-truth observation grids:
    - Critical Success Index (CSI / Threat Score)
    - Probability of Detection (POD / Hit Rate)
    - False Alarm Ratio (FAR)
    - Heidke Skill Score (HSS)
    - Brier Score (BS for calibrated probabilistic forecasts)
    - Root Mean Square Error (RMSE) & Mean Absolute Error (MAE)
================================================================================
"""

import math
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import torch


def contingency_table(
    pred_binary: np.ndarray,
    target_binary: np.ndarray
) -> Tuple[int, int, int, int]:
    """
    Computes 2x2 contingency matrix: (Hits, False Alarms, Misses, Correct Negatives).
    """
    hits = int(np.sum((pred_binary == 1) & (target_binary == 1)))
    false_alarms = int(np.sum((pred_binary == 1) & (target_binary == 0)))
    misses = int(np.sum((pred_binary == 0) & (target_binary == 1)))
    correct_negatives = int(np.sum((pred_binary == 0) & (target_binary == 0)))
    return hits, false_alarms, misses, correct_negatives


def compute_csi(hits: int, false_alarms: int, misses: int) -> float:
    """Critical Success Index (CSI = Hits / (Hits + Misses + False Alarms))."""
    denom = hits + misses + false_alarms
    if denom == 0:
        return 1.0  # Perfect score if no events predicted or observed
    return round(float(hits / denom), 4)


def compute_pod(hits: int, misses: int) -> float:
    """Probability of Detection (POD = Hits / (Hits + Misses))."""
    denom = hits + misses
    if denom == 0:
        return 1.0
    return round(float(hits / denom), 4)


def compute_far(hits: int, false_alarms: int) -> float:
    """False Alarm Ratio (FAR = False Alarms / (Hits + False Alarms))."""
    denom = hits + false_alarms
    if denom == 0:
        return 0.0
    return round(float(false_alarms / denom), 4)


def compute_hss(hits: int, false_alarms: int, misses: int, correct_negatives: int) -> float:
    """Heidke Skill Score (HSS)."""
    total = hits + false_alarms + misses + correct_negatives
    if total == 0:
        return 0.0
    expected_correct = ((hits + misses) * (hits + false_alarms) + (correct_negatives + misses) * (correct_negatives + false_alarms)) / total
    denom = total - expected_correct
    if denom == 0:
        return 0.0
    hss = (hits + correct_negatives - expected_correct) / denom
    return round(float(hss), 4)


def compute_brier_score(prob_pred: np.ndarray, target_binary: np.ndarray) -> float:
    """Brier Score = Mean squared difference between predicted probability and binary outcome."""
    if prob_pred.size == 0 or target_binary.size == 0:
        return 0.0
    bs = float(np.mean((prob_pred - target_binary) ** 2))
    return round(bs, 4)


def compute_rmse_and_mae(pred_grid: np.ndarray, target_grid: np.ndarray) -> Tuple[float, float]:
    """Calculates continuous RMSE and MAE."""
    diff = pred_grid - target_grid
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    mae = float(np.mean(np.abs(diff)))
    return round(rmse, 3), round(mae, 3)


def evaluate_forecast_vs_target(
    pred_grid: Union[np.ndarray, List[List[float]]],
    target_grid: Union[np.ndarray, List[List[float]]],
    threshold_dbz: float = 35.0,
    prob_threshold: float = 0.50
) -> Dict[str, Any]:
    """
    Evaluates dynamic prediction grid vs ground truth target grid.
    """
    pred_arr = np.array(pred_grid, dtype=np.float32)
    target_arr = np.array(target_grid, dtype=np.float32)

    # Binary convective event masks
    pred_bin = (pred_arr >= threshold_dbz).astype(np.int32)
    target_bin = (target_arr >= threshold_dbz).astype(np.int32)

    hits, false_alarms, misses, correct_negatives = contingency_table(pred_bin, target_bin)
    csi = compute_csi(hits, false_alarms, misses)
    pod = compute_pod(hits, misses)
    far = compute_far(hits, false_alarms)
    hss = compute_hss(hits, false_alarms, misses, correct_negatives)
    rmse, mae = compute_rmse_and_mae(pred_arr, target_arr)

    # Calibrated probability grid vs binary truth
    prob_grid = 1.0 / (1.0 + np.exp(-(np.clip(pred_arr, 0.0, 70.0) - 38.0) / 6.0))
    prob_grid[pred_arr < 15.0] = 0.0
    brier = compute_brier_score(prob_grid, target_bin)

    return {
        "evaluation_status": "CALCULATED_FROM_GROUND_TRUTH",
        "threshold_dbz": threshold_dbz,
        "contingency": {
            "hits": hits,
            "false_alarms": false_alarms,
            "misses": misses,
            "correct_negatives": correct_negatives
        },
        "metrics": {
            "csi": csi,
            "pod": pod,
            "far": far,
            "hss": hss,
            "brier_score": brier,
            "rmse_dbz": rmse,
            "mae_dbz": mae
        }
    }
