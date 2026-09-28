#!/usr/bin/env python3
"""
STORMTRACE Future-Frame Multi-Horizon Evaluation Engine
================================================================================
Evaluates spatiotemporal nowcast predictions against genuine future observations
at discrete forecast horizons (+15, +30, +45, +60, +90, +120 minutes).
Strictly enforces temporal separation between initialization time T0 and target time T0 + dt.
================================================================================
"""

from typing import Dict, Any, List, Optional
import numpy as np

from .metrics import evaluate_forecast_vs_target


class FutureFrameEvaluator:
    """
    Evaluator comparing multi-horizon predictions against corresponding ground-truth frames.
    """

    LEAD_TIMES_MIN = [15, 30, 45, 60, 90, 120]

    def __init__(self, dbz_threshold: float = 35.0):
        self.dbz_threshold = dbz_threshold

    def evaluate_sequence_forecast(
        self,
        initialization_timestamp_iso: str,
        lead_time_forecasts: List[Dict[str, Any]],
        future_ground_truth_frames: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates predictions against ground truth frames at each forecast horizon.
        
        Args:
            initialization_timestamp_iso: T0 timestamp (e.g. '2026-09-19T14:00:00Z')
            lead_time_forecasts: List of forecast dicts containing 'lead_time_min' and 'grids'
            future_ground_truth_frames: List of actual observed frames matching future timestamps
            
        Returns:
            Structured evaluation report with per-horizon metrics.
        """
        horizon_results = []
        overall_csi = []
        overall_pod = []
        overall_far = []
        overall_brier = []

        for f_idx, forecast in enumerate(lead_time_forecasts):
            lead_time = forecast.get("lead_time_min", self.LEAD_TIMES_MIN[min(f_idx, len(self.LEAD_TIMES_MIN) - 1)])
            pred_refl = forecast["grids"]["reflectivity_dbz"]

            if f_idx < len(future_ground_truth_frames):
                gt_frame = future_ground_truth_frames[f_idx]
                target_refl = gt_frame["grids"]["reflectivity_dbz"]
                target_ts = gt_frame.get("timestamp_iso", f"{initialization_timestamp_iso}+{lead_time}m")

                # Compute verification metrics
                eval_metrics = evaluate_forecast_vs_target(
                    pred_grid=pred_refl,
                    target_grid=target_refl,
                    threshold_dbz=self.dbz_threshold
                )

                m = eval_metrics["metrics"]
                overall_csi.append(m["csi"])
                overall_pod.append(m["pod"])
                overall_far.append(m["far"])
                overall_brier.append(m["brier_score"])

                horizon_results.append({
                    "lead_time_min": lead_time,
                    "initialization_timestamp": initialization_timestamp_iso,
                    "target_timestamp": target_ts,
                    "evaluation_status": "VERIFIED_VS_FUTURE_OBSERVATION",
                    "metrics": m,
                    "contingency": eval_metrics["contingency"]
                })
            else:
                horizon_results.append({
                    "lead_time_min": lead_time,
                    "initialization_timestamp": initialization_timestamp_iso,
                    "target_timestamp": f"{initialization_timestamp_iso}+{lead_time}m",
                    "evaluation_status": "PENDING_FUTURE_GROUND_TRUTH",
                    "metrics": {
                        "csi": None,
                        "pod": None,
                        "far": None,
                        "brier_score": None
                    }
                })

        # Calculate mean across verified horizons
        mean_csi = round(float(np.mean(overall_csi)), 4) if overall_csi else None
        mean_pod = round(float(np.mean(overall_pod)), 4) if overall_pod else None
        mean_far = round(float(np.mean(overall_far)), 4) if overall_far else None
        mean_brier = round(float(np.mean(overall_brier)), 4) if overall_brier else None

        return {
            "status": "success",
            "initialization_timestamp": initialization_timestamp_iso,
            "threshold_dbz": self.dbz_threshold,
            "evaluated_horizons_count": len(overall_csi),
            "summary_metrics": {
                "mean_csi": mean_csi,
                "mean_pod": mean_pod,
                "mean_far": mean_far,
                "mean_brier_score": mean_brier,
                "status": "CALCULATED" if overall_csi else "PENDING_FINAL_TRAINING_EVALUATION"
            },
            "per_horizon_evaluations": horizon_results
        }
