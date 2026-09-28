#!/usr/bin/env python3
"""
STORMTRACE PyTorch ConvLSTM Training Engine & Loss Functions
================================================================================
Provides a clean training and validation harness for the genuine PyTorch
Spatiotemporal ConvLSTM forecasting neural network.

Features:
    - Weighted Convective Loss (penalizes high-reflectivity convective core errors)
    - Chronological DataLoader integration
    - Metric tracking across all 6 forecast horizons (+15m to +120m)
    - Learning rate scheduling & early checkpoint saving
    - Strict data governance & domain compatibility gating
================================================================================
"""

import os
import sys
import random
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.models.spatiotemporal_model import SpatiotemporalForecastNet, ModelConfig
from ml.datasets.temporal_radar_dataset import TemporalRadarDataset, create_dataloaders


class WeightedConvectiveLoss(nn.Module):
    """
    Weighted Mean Squared Error (WMSE) / Smooth L1 loss tailored for convective nowcasting.
    
    Assigns higher penalty weights to intense convective storm cores (reflectivity >= 35 dBZ,
    or normalized intensity >= 0.50) to prevent the model from trivializing severe storms
    into diffuse low-dBZ background.
    
    Formula:
        weight(y) = 1.0 + (convective_weight - 1.0) * (y >= threshold)
        Loss = mean( weight(y) * (y - y_hat)^2 )
    """

    def __init__(
        self,
        convective_weight: float = 4.0,
        dbz_threshold_norm: float = 0.50, # 35 dBZ / 70 dBZ
        loss_type: str = "mse"
    ):
        super().__init__()
        self.convective_weight = convective_weight
        self.dbz_threshold_norm = dbz_threshold_norm
        self.loss_type = loss_type

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pred: Predicted tensor [B, T_out, C, H, W]
            target: Ground truth tensor [B, T_out, C, H, W]
        Returns:
            Weighted scalar loss
        """
        # Convective weighting mask
        weight_mask = torch.ones_like(target)
        convective_mask = target >= self.dbz_threshold_norm
        weight_mask[convective_mask] = self.convective_weight

        if self.loss_type == "smooth_l1":
            diff = nn.functional.smooth_l1_loss(pred, target, reduction="none")
        else:
            diff = (pred - target) ** 2

        weighted_loss = weight_mask * diff
        return weighted_loss.mean()


class ConvLSTMTrainer:
    """
    Training manager for Spatiotemporal ConvLSTM forecasting models.
    """

    def __init__(
        self,
        model: Optional[SpatiotemporalForecastNet] = None,
        config: Optional[ModelConfig] = None,
        loss_fn: Optional[nn.Module] = None,
        lr: float = 1e-3,
        weight_decay: float = 1e-5,
        checkpoint_dir: str = "ml/models",
        device: Optional[str] = None,
        seed: int = 42
    ):
        self.seed = seed
        self._set_seed(seed)

        self.config = config or ModelConfig()
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = (model or SpatiotemporalForecastNet(self.config)).to(self.device)
        self.loss_fn = loss_fn or WeightedConvectiveLoss(convective_weight=4.0)

        self.lr = lr
        self.optimizer = optim.AdamW(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, mode="min", factor=0.5, patience=3)
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        self.history: List[Dict[str, Any]] = []

    def _set_seed(self, seed: int):
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def train_epoch(self, train_loader: DataLoader) -> float:
        """Executes one training epoch over batches."""
        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for input_batch, target_batch in train_loader:
            input_batch = input_batch.to(self.device)   # [B, T_in, C, H, W]
            target_batch = target_batch.to(self.device) # [B, T_out, C, H, W]

            self.optimizer.zero_grad()
            predictions = self.model(input_batch, future_steps=target_batch.shape[1])
            loss = self.loss_fn(predictions, target_batch)

            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=2.0)
            self.optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        return total_loss / max(1, n_batches)

    def validate_epoch(self, val_loader: DataLoader) -> Tuple[float, Dict[int, float]]:
        """Evaluates model performance across validation set and per-horizon error."""
        self.model.eval()
        total_loss = 0.0
        n_batches = 0
        lead_times = self.config.lead_times_min
        horizon_errors = {lt: 0.0 for lt in lead_times}

        with torch.no_grad():
            for input_batch, target_batch in val_loader:
                input_batch = input_batch.to(self.device)
                target_batch = target_batch.to(self.device)

                predictions = self.model(input_batch, future_steps=target_batch.shape[1])
                loss = self.loss_fn(predictions, target_batch)
                total_loss += loss.item()

                # Calculate per-horizon MSE
                for step_idx, lt in enumerate(lead_times):
                    if step_idx < target_batch.shape[1]:
                        step_mse = nn.functional.mse_loss(
                            predictions[:, step_idx, :, :, :],
                            target_batch[:, step_idx, :, :, :]
                        ).item()
                        horizon_errors[lt] += step_mse

                n_batches += 1

        avg_loss = total_loss / max(1, n_batches)
        for lt in horizon_errors:
            horizon_errors[lt] /= max(1, n_batches)

        return avg_loss, horizon_errors

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 5,
        checkpoint_name: str = "convlstm_checkpoint.pt"
    ) -> Dict[str, Any]:
        """Runs multi-epoch training loop with validation and checkpoint saving."""
        best_val_loss = float("inf")
        ckpt_path = os.path.join(self.checkpoint_dir, checkpoint_name)

        print(f"\n--- Starting ConvLSTM Training ({epochs} epochs, device={self.device}) ---")
        for epoch in range(1, epochs + 1):
            train_loss = self.train_epoch(train_loader)
            val_loss, horizon_mses = self.validate_epoch(val_loader)
            self.scheduler.step(val_loss)

            epoch_record = {
                "epoch": epoch,
                "train_loss": round(train_loss, 5),
                "val_loss": round(val_loss, 5),
                "horizon_mses": {k: round(v, 5) for k, v in horizon_mses.items()},
                "lr": self.optimizer.param_groups[0]["lr"]
            }
            self.history.append(epoch_record)
            print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.model.save_checkpoint(
                    ckpt_path,
                    optimizer=self.optimizer,
                    epoch=epoch,
                    extra_metadata={"best_val_loss": best_val_loss, "history": self.history}
                )

        return {
            "status": "completed",
            "epochs": epochs,
            "best_val_loss": best_val_loss,
            "checkpoint_path": ckpt_path,
            "history": self.history
        }


def check_east_india_training_eligibility(dataset: TemporalRadarDataset) -> Tuple[bool, str]:
    """
    Enforces scientific data governance rule:
    Only genuine 2020+ East India DWR radar files may be used for final model training.
    """
    if len(dataset) == 0:
        return False, "Training blocked: Dataset contains 0 samples."

    sample_meta = dataset.get_sample_with_metadata(0)["metadata"]
    domain = sample_meta.provenance.get("domain", "")
    is_real = sample_meta.provenance.get("is_real", False)
    t0_str = sample_meta.t0_timestamp

    if not is_real:
        return False, "Training blocked: Dataset is synthetic benchmark simulation, not real operational data."

    if "TERLS" in domain or "SOUTH_INDIA" in domain:
        return False, (
            "Training blocked: Dataset is 2018 ISRO TERLS DWR (South India / Kerala), "
            "which does NOT cover the target Regional East India domain (83.5E-89.8E, 20.0N-26.3N). "
            "TERLS is reserved for radar-ingestion pipeline validation only."
        )

    if not sample_meta.is_domain_compatible:
        return False, f"Training blocked: Dataset domain '{domain}' is not compatible with Regional East India."

    return True, "Eligible for final East India training."


if __name__ == "__main__":
    print("STORMTRACE PyTorch ConvLSTM Training Harness initialized.")
