#!/usr/bin/env python3
"""
STORMTRACE Model Evaluation & Baseline Comparison Harness
================================================================================
⚠️ EVALUATION & PROVENANCE DISCLOSURE:
This harness evaluates the Trained Multimodal Model against Optical Flow and
Persistence Baselines strictly on the held-out test sequence using true future
verification targets (T0 + 15m, T0 + 30m, T0 + 45m, T0 + 60m, T0 + 90m, T0 + 120m).

Under NO circumstance is a future forecast evaluated against the initialization frame (T0).
If future ground truth is unavailable, the metric is reported as UNAVAILABLE.
================================================================================
"""

import os
import sys
import json
import csv
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

try:
    from dataset.grid import StormTraceGrid
    from ml.provenance import DataType
    from ml.train_model import MultimodalNowcastTrainer, derive_convective_proxy_label
except ImportError:
    from stormtrace.data.grid import StormTraceGrid
    from stormtrace.data.provenance import DataType
    from scripts.train_model import MultimodalNowcastTrainer, derive_convective_proxy_label


LEAD_TIMES_MIN = [15, 30, 45, 60, 90, 120]


def compute_contingency_metrics(
    pred_prob: List[List[float]],
    target_binary: List[List[int]],
    prob_threshold: float = 0.30
) -> Dict[str, Any]:
    """
    Computes 2x2 contingency table (Hits, Misses, False Alarms, Correct Negatives)
    and derives standard meteorological skill scores (POD, FAR, CSI, HSS, Brier Score).
    """
    h = len(pred_prob)
    w = len(pred_prob[0])

    hits = 0
    misses = 0
    false_alarms = 0
    correct_negatives = 0
    brier_sum = 0.0

    for j in range(h):
        for i in range(w):
            p = pred_prob[j][i]
            y = target_binary[j][i]
            brier_sum += (p - y) ** 2

            pred_bin = 1 if p >= prob_threshold else 0
            if pred_bin == 1 and y == 1:
                hits += 1
            elif pred_bin == 0 and y == 1:
                misses += 1
            elif pred_bin == 1 and y == 0:
                false_alarms += 1
            else:
                correct_negatives += 1

    total = h * w
    pod = hits / max(1, hits + misses) if (hits + misses) > 0 else 0.0
    far = false_alarms / max(1, hits + false_alarms) if (hits + false_alarms) > 0 else 0.0
    csi = hits / max(1, hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else 0.0

    # Heidke Skill Score (HSS)
    expected_correct = ((hits + misses) * (hits + false_alarms) + (misses + correct_negatives) * (false_alarms + correct_negatives)) / max(1, total)
    hss_den = (total - expected_correct)
    hss = (hits + correct_negatives - expected_correct) / hss_den if hss_den != 0 else 0.0
    brier_score = brier_sum / max(1, total)

    return {
        "hits": hits,
        "misses": misses,
        "false_alarms": false_alarms,
        "correct_negatives": correct_negatives,
        "pod": round(pod, 3),
        "far": round(far, 3),
        "csi": round(csi, 3),
        "hss": round(hss, 3),
        "brier_score": round(brier_score, 4)
    }


def persistence_forecast(
    base_refl: List[List[float]],
    lead_time_min: int = 30,
    dbz_threshold: float = 38.0
) -> List[List[float]]:
    """
    Persistence baseline: Simply persists the T0 observed state forward.
    Predicted probability is 1.0 for pixels >= 38 dBZ at T0, 0.0 otherwise.
    Evaluated strictly against the future observation at T0 + lead_time.
    """
    h = len(base_refl)
    w = len(base_refl[0])
    prob_grid = [[0.0 for _ in range(w)] for _ in range(h)]
    for j in range(h):
        for i in range(w):
            val = base_refl[j][i]
            prob_grid[j][i] = 1.0 if val >= dbz_threshold else 0.0
    return prob_grid


def optical_flow_extrapolation_forecast(
    base_refl: List[List[float]],
    lead_time_min: int = 30,
    vx: float = 1.3,
    vy: float = -0.3,
    dbz_threshold: float = 38.0
) -> List[List[float]]:
    """
    Optical flow extrapolation baseline: Advects T0 field forward along estimated
    velocity vector with physical convective decay across lead times.
    Evaluated strictly against the future observation at T0 + lead_time.
    """
    h = len(base_refl)
    w = len(base_refl[0])
    steps_ahead = lead_time_min / 5.0
    shift_x = vx * steps_ahead * 0.15
    shift_y = vy * steps_ahead * 0.15
    decay = max(0.25, 1.0 - (lead_time_min - 15) * 0.005)

    prob_grid = [[0.0 for _ in range(w)] for _ in range(h)]
    for j in range(h):
        for i in range(w):
            src_x = int(round(i - shift_x))
            src_y = int(round(j - shift_y))
            if 0 <= src_x < w and 0 <= src_y < h:
                val = base_refl[src_y][src_x] * decay
                prob_grid[j][i] = 1.0 if val >= dbz_threshold else (0.4 if val >= 30.0 else 0.0)
    return prob_grid


def run_evaluation() -> Dict[str, Any]:
    trainer = MultimodalNowcastTrainer()
    train_set, val_set, test_set = trainer.load_dataset_splits()

    # Load trained checkpoint parameters
    checkpoint_path = "ml/models/stormtrace_multimodal_best.json" if os.path.exists("ml/models/stormtrace_multimodal_best.json") else "models/stormtrace_multimodal_best.json"
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as fp:
            chk = json.load(fp)
            trainer.params = chk.get("parameters", trainer.params)
            print(f"Loaded trained checkpoint: {checkpoint_path}")
    else:
        print("No checkpoint found; training model first...")
        trainer.train()

    print("\n================================================================================")
    print("📊 STORMTRACE MODEL & BASELINE EVALUATION (SYNTHETIC HELD-OUT TEST SEQUENCE)")
    print("================================================================================")
    print(f"Evaluation Mode: SYNTHETIC BENCHMARK EVALUATION (Held-out Test Scenario)")
    print(f"Test Windows   : {len(test_set)} Multi-Horizon Sequence Windows")
    print(f"Target Strategy: STRICT FUTURE GROUND TRUTH (T0 + Lead Time)")
    print("--------------------------------------------------------------------------------\n")

    results_by_lead_time = {}
    csv_rows = []

    for lt in LEAD_TIMES_MIN:
        model_metrics_list = []
        pers_metrics_list = []
        opt_metrics_list = []

        valid_windows = 0
        for sample in test_set:
            tgt_info = sample["future_targets"].get(lt)
            if not tgt_info or not tgt_info.get("available"):
                # Future ground truth is unavailable for this window; skip (do NOT evaluate against T0)
                continue

            target_grid = tgt_info["target_binary"]
            refl_grid = sample["tensors"]["radar_reflectivity_dbz"]

            # 1. Trained Multimodal Extrapolation Model
            pred_model = trainer.forward_predict_proba(sample, lead_time_min=lt)
            m_metrics = compute_contingency_metrics(pred_model, target_grid, prob_threshold=0.30)
            model_metrics_list.append(m_metrics)

            # 2. Persistence Baseline (T0 persisted -> evaluated vs T0+LT future ground truth)
            pred_pers = persistence_forecast(refl_grid, lead_time_min=lt)
            p_metrics = compute_contingency_metrics(pred_pers, target_grid, prob_threshold=0.50)
            pers_metrics_list.append(p_metrics)

            # 3. Optical Flow Extrapolation Baseline (T0 advected -> evaluated vs T0+LT future ground truth)
            pred_opt = optical_flow_extrapolation_forecast(refl_grid, lead_time_min=lt)
            o_metrics = compute_contingency_metrics(pred_opt, target_grid, prob_threshold=0.30)
            opt_metrics_list.append(o_metrics)

            valid_windows += 1

        if valid_windows > 0:
            avg_model = {k: round(sum(m[k] for m in model_metrics_list) / len(model_metrics_list), 3) for k in ["pod", "far", "csi", "hss", "brier_score"]}
            avg_pers = {k: round(sum(m[k] for m in pers_metrics_list) / len(pers_metrics_list), 3) for k in ["pod", "far", "csi", "hss", "brier_score"]}
            avg_opt = {k: round(sum(m[k] for m in opt_metrics_list) / len(opt_metrics_list), 3) for k in ["pod", "far", "csi", "hss", "brier_score"]}
        else:
            avg_model = {"pod": "UNAVAILABLE", "far": "UNAVAILABLE", "csi": "UNAVAILABLE", "hss": "UNAVAILABLE", "brier_score": "UNAVAILABLE"}
            avg_pers = {"pod": "UNAVAILABLE", "far": "UNAVAILABLE", "csi": "UNAVAILABLE", "hss": "UNAVAILABLE", "brier_score": "UNAVAILABLE"}
            avg_opt = {"pod": "UNAVAILABLE", "far": "UNAVAILABLE", "csi": "UNAVAILABLE", "hss": "UNAVAILABLE", "brier_score": "UNAVAILABLE"}

        results_by_lead_time[f"+{lt}min"] = {
            "valid_evaluation_windows": valid_windows,
            "trained_multimodal_model": avg_model,
            "optical_flow_baseline": avg_opt,
            "persistence_baseline": avg_pers
        }

        csv_rows.append({
            "lead_time_min": lt,
            "valid_windows": valid_windows,
            "model_pod": avg_model["pod"],
            "model_far": avg_model["far"],
            "model_csi": avg_model["csi"],
            "model_hss": avg_model["hss"],
            "model_brier": avg_model["brier_score"],
            "optical_flow_csi": avg_opt["csi"],
            "persistence_csi": avg_pers["csi"]
        })

    # Print Formatted Skill Table
    print("┌──────────────┬───────────────────────────────┬───────────────────────────────┬───────────────────────────────┐")
    print("│  Lead Time   │   Trained Multimodal Model    │    Optical Flow Extrap        │     Persistence Baseline      │")
    print("│   (Horizon)  │  CSI    POD    FAR    HSS     │  CSI    POD    FAR    HSS     │  CSI    POD    FAR    HSS     │")
    print("├──────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────┤")
    for lt in LEAD_TIMES_MIN:
        key = f"+{lt}min"
        m = results_by_lead_time[key]["trained_multimodal_model"]
        o = results_by_lead_time[key]["optical_flow_baseline"]
        p = results_by_lead_time[key]["persistence_baseline"]
        if isinstance(m["csi"], float):
            print(f"│  +{lt:3d} min     │ {m['csi']:.3f}  {m['pod']:.3f}  {m['far']:.3f}  {m['hss']:.3f}  │ {o['csi']:.3f}  {o['pod']:.3f}  {o['far']:.3f}  {o['hss']:.3f}  │ {p['csi']:.3f}  {p['pod']:.3f}  {p['far']:.3f}  {p['hss']:.3f}  │")
        else:
            print(f"│  +{lt:3d} min     │ UNAVAILABLE                   │ UNAVAILABLE                   │ UNAVAILABLE                   │")
    print("└──────────────┴───────────────────────────────┴───────────────────────────────┴───────────────────────────────┘\n")

    # Save to JSON & CSV in docs/evaluation and mirror to evaluation/
    os.makedirs("docs/evaluation", exist_ok=True)
    os.makedirs("evaluation", exist_ok=True)
    json_path = "docs/evaluation/evaluation_metrics.json"
    eval_payload = {
        "evaluation_title": "STORMTRACE Model & Baseline Evaluation (Synthetic Benchmark Sequences)",
        "evaluation_type": "SYNTHETIC_BENCHMARK_EVALUATION",
        "evaluated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "test_scenario": "global_tropical_cyclone_band",
        "test_windows_count": len(test_set),
        "lead_time_metrics": results_by_lead_time,
        "disclaimer": "Evaluated on multi-timestep synthetic benchmark convective storm sequences. Real operational validation requires verified radar/satellite archive sequences."
    }

    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(eval_payload, fp, indent=2)

    with open("evaluation/evaluation_metrics.json", "w", encoding="utf-8") as fp:
        json.dump(eval_payload, fp, indent=2)

    csv_path = "docs/evaluation/evaluation_metrics.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["lead_time_min", "valid_windows", "model_pod", "model_far", "model_csi", "model_hss", "model_brier", "optical_flow_csi", "persistence_csi"])
        writer.writeheader()
        writer.writerows(csv_rows)

    with open("evaluation/evaluation_metrics.csv", "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["lead_time_min", "valid_windows", "model_pod", "model_far", "model_csi", "model_hss", "model_brier", "optical_flow_csi", "persistence_csi"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"📄 Saved evaluation metrics table to: {csv_path}")
    print(f"💾 Saved evaluation metrics JSON to : {json_path}")
    print("================================================================================\n")

    return eval_payload


if __name__ == "__main__":
    run_evaluation()
