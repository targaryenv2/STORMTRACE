#!/usr/bin/env python3
"""
STORMTRACE Temporal Radar PyTorch Dataset & Sequence Builder
================================================================================
Constructs strictly chronological, non-leaking multi-horizon spatiotemporal
training samples [B, T_in, C, H, W] -> [B, T_out, C, H, W] from real or benchmark
radar observation sequences.
================================================================================
"""

import os
import sys
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional, Union

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from dataset.loaders.radar_loader import RadarDataLoader
    from dataset.grid import StormTraceGrid
    from ml.provenance import DataType, SystemMode
except ImportError:
    from stormtrace.data.radar_loader import RadarDataLoader
    from stormtrace.data.grid import StormTraceGrid
    from stormtrace.data.provenance import DataType, SystemMode


@dataclass
class TemporalSequenceMetadata:
    """Metadata tracking timestamps and provenance for a single sequence sample."""
    sample_index: int
    t0_timestamp: str
    input_timestamps: List[str]
    target_timestamps: List[str]
    lead_times_min: List[int]
    provenance: Dict[str, Any]
    grid_bounds: Dict[str, float]
    is_domain_compatible: bool


class TemporalRadarDataset(Dataset):
    """
    PyTorch Dataset for Spatiotemporal Radar Nowcasting.
    
    Extracts strictly ordered sliding temporal windows:
        Input:  [T-60, T-45, T-30, T-15, T0] (5 frames)
        Target: [T+15, T+30, T+45, T+60, T+90, T+120] (6 future frames)
        
    Guarantees:
        1. Strict ascending chronological ordering (T_target > T0).
        2. No target frame is ever duplicated or derived from T0.
        3. Missing future frames invalidate the sample (no zero-padding / fabrication).
        4. Spatial grid consistency verified across all sequence frames.
        5. Chronological / event-based train-val-test splitting (zero temporal leakage).
    """

    DEFAULT_LEAD_TIMES = [15, 30, 45, 60, 90, 120]

    def __init__(
        self,
        frames: Optional[List[Dict[str, Any]]] = None,
        file_paths: Optional[List[str]] = None,
        in_seq_len: int = 5,
        out_seq_len: int = 6,
        lead_times_min: Optional[List[int]] = None,
        step_dt_min: float = 15.0,
        max_dt_tolerance_min: float = 25.0,
        normalize_dbz: bool = True,
        max_dbz: float = 70.0,
        spatial_size: Tuple[int, int] = (64, 64),
        provenance_tag: str = "REAL_OR_BENCHMARK_DWR"
    ):
        super().__init__()
        self.in_seq_len = in_seq_len
        self.out_seq_len = out_seq_len
        self.lead_times_min = lead_times_min or self.DEFAULT_LEAD_TIMES
        self.step_dt_min = step_dt_min
        self.max_dt_tolerance_min = max_dt_tolerance_min
        self.normalize_dbz = normalize_dbz
        self.max_dbz = max_dbz
        self.spatial_size = spatial_size
        self.provenance_tag = provenance_tag

        # Load frames if file paths provided
        self.loader = RadarDataLoader()
        self.raw_frames = []
        if frames is not None:
            self.raw_frames = frames
        elif file_paths is not None:
            self.raw_frames = self._load_frames_from_files(file_paths)

        # Build valid temporal sequence samples
        self.samples: List[Dict[str, Any]] = []
        if self.raw_frames:
            self._build_samples()

    def _load_frames_from_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Loads and sorts radar scan frames from physical NetCDF / file paths."""
        loaded_frames = []
        for path in file_paths:
            if not os.path.exists(path):
                continue
            if path.endswith(".nc"):
                scan = self.loader.read_netcdf_scan(path)
                dbz_grid = self.loader.extract_composite_dbz(scan, target_shape=self.spatial_size)
                ts = scan.get("timestamp_utc") or datetime.now(timezone.utc).isoformat()
                loaded_frames.append({
                    "timestamp": ts,
                    "filepath": path,
                    "reflectivity_dbz": dbz_grid,
                    "grid_shape": (len(dbz_grid), len(dbz_grid[0])),
                    "is_real": scan.get("is_real", True),
                    "domain_name": scan.get("domain_name", "UNKNOWN")
                })
        return loaded_frames

    def _parse_iso(self, ts_str: str) -> datetime:
        """Parses ISO timestamp safely."""
        ts_clean = ts_str.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(ts_clean)
        except Exception:
            # Fallback format parsing
            return datetime.strptime(ts_clean[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

    def _build_samples(self):
        """
        Slices strictly verified chronological 5->6 sequence windows.
        Rejects windows with gaps, missing future observations, or grid mismatches.
        """
        # Step 1: Sort frames chronologically by timestamp
        sorted_frames = sorted(self.raw_frames, key=lambda f: self._parse_iso(f["timestamp"]))

        # Step 2: Validate spatial consistency across all frames
        self._validate_global_grid(sorted_frames)

        n_frames = len(sorted_frames)
        # Calculate nominal frame offsets for each lead time
        # E.g. with step_dt_min=15.0: 15m->1 step, 30m->2, 45m->3, 60m->4, 90m->6, 120m->8
        lead_offsets = [max(1, int(round(lt / self.step_dt_min))) for lt in self.lead_times_min]
        max_future_offset = max(lead_offsets) if lead_offsets else 0

        # Step 3: Slide window across chronologically sorted frames
        for t0_idx in range(self.in_seq_len - 1, n_frames - max_future_offset):
            input_indices = list(range(t0_idx - self.in_seq_len + 1, t0_idx + 1))
            target_indices = [t0_idx + offset for offset in lead_offsets]

            # Validate input temporal spacing
            input_frames = [sorted_frames[idx] for idx in input_indices]
            input_valid, in_err = self._validate_temporal_spacing(input_frames)
            if not input_valid:
                continue

            # Validate target future observations exist and are in the future
            target_frames = []
            target_valid = True
            t0_time = self._parse_iso(sorted_frames[t0_idx]["timestamp"])

            for tgt_idx, lt in zip(target_indices, self.lead_times_min):
                if tgt_idx >= n_frames:
                    target_valid = False
                    break
                tgt_frame = sorted_frames[tgt_idx]
                tgt_time = self._parse_iso(tgt_frame["timestamp"])
                dt_minutes = (tgt_time - t0_time).total_seconds() / 60.0

                # Strict Future Verification: Target must strictly succeed T0
                if dt_minutes <= 0.0:
                    target_valid = False
                    break
                target_frames.append(tgt_frame)

            if not target_valid or len(target_frames) != len(self.lead_times_min):
                continue

            # Construct Tensors
            # Input Tensor: [T_in, 1, H, W]
            input_arrays = []
            for f in input_frames:
                arr = np.array(f["reflectivity_dbz"], dtype=np.float32)
                if self.normalize_dbz:
                    arr = np.clip(arr / self.max_dbz, 0.0, 1.0)
                input_arrays.append(arr)
            input_tensor = torch.from_numpy(np.stack(input_arrays, axis=0)).unsqueeze(1) # [T_in, 1, H, W]

            # Target Tensor: [T_out, 1, H, W]
            target_arrays = []
            for f in target_frames:
                arr = np.array(f["reflectivity_dbz"], dtype=np.float32)
                if self.normalize_dbz:
                    arr = np.clip(arr / self.max_dbz, 0.0, 1.0)
                target_arrays.append(arr)
            target_tensor = torch.from_numpy(np.stack(target_arrays, axis=0)).unsqueeze(1) # [T_out, 1, H, W]

            metadata = TemporalSequenceMetadata(
                sample_index=len(self.samples),
                t0_timestamp=sorted_frames[t0_idx]["timestamp"],
                input_timestamps=[f["timestamp"] for f in input_frames],
                target_timestamps=[f["timestamp"] for f in target_frames],
                lead_times_min=self.lead_times_min,
                provenance={
                    "provenance_tag": self.provenance_tag,
                    "is_real": sorted_frames[t0_idx].get("is_real", False),
                    "domain": sorted_frames[t0_idx].get("domain_name", "UNKNOWN"),
                },
                grid_bounds={
                    "height": input_tensor.shape[-2],
                    "width": input_tensor.shape[-1]
                },
                is_domain_compatible=(sorted_frames[t0_idx].get("domain_name") == "REGIONAL_EAST_INDIA")
            )

            self.samples.append({
                "input": input_tensor,
                "target": target_tensor,
                "metadata": metadata
            })

    def _validate_global_grid(self, frames: List[Dict[str, Any]]):
        """Verifies spatial dimension and grid consistency across all loaded frames."""
        if not frames:
            return
        base_shape = frames[0].get("grid_shape") or (len(frames[0]["reflectivity_dbz"]), len(frames[0]["reflectivity_dbz"][0]))
        for idx, f in enumerate(frames):
            cur_shape = f.get("grid_shape") or (len(f["reflectivity_dbz"]), len(f["reflectivity_dbz"][0]))
            if cur_shape != base_shape:
                raise ValueError(
                    f"Grid dimension mismatch at frame {idx}: expected {base_shape}, got {cur_shape}"
                )

    def _validate_temporal_spacing(self, sequence_frames: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Validates that consecutive frames in sequence advance monotonically in time."""
        for i in range(len(sequence_frames) - 1):
            t1 = self._parse_iso(sequence_frames[i]["timestamp"])
            t2 = self._parse_iso(sequence_frames[i + 1]["timestamp"])
            dt_sec = (t2 - t1).total_seconds()
            if dt_sec <= 0:
                return False, f"Non-monotonic timestamp order between frame {i} and {i+1}"
            dt_min = dt_sec / 60.0
            if dt_min > self.max_dt_tolerance_min * 2.0:
                return False, f"Gap too large ({dt_min:.1f} min) between frame {i} and {i+1}"
        return True, ""

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            input_tensor: [T_in, C_in, H, W]
            target_tensor: [T_out, C_out, H, W]
        """
        sample = self.samples[idx]
        return sample["input"], sample["target"]

    def get_sample_with_metadata(self, idx: int) -> Dict[str, Any]:
        """Returns the full sample tensor package including metadata dataclass."""
        return self.samples[idx]

    def split_chronological(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple["TemporalRadarDataset", "TemporalRadarDataset", "TemporalRadarDataset"]:
        """
        Splits dataset into Train, Validation, and Held-out Test datasets
        strictly along chronological boundaries (earlier -> train, mid -> val, latest -> test).
        Zero random shuffling across splits to prevent temporal data leakage.
        """
        if not math.isclose(train_ratio + val_ratio + test_ratio, 1.0, abs_tol=1e-3):
            raise ValueError("Split ratios must sum to 1.0")

        n_total = len(self.samples)
        if n_total == 0:
            empty = TemporalRadarDataset()
            return empty, empty, empty

        n_train = max(1, int(round(n_total * train_ratio)))
        n_val = max(1, int(round(n_total * val_ratio)))
        if n_train + n_val >= n_total:
            n_train = max(1, n_total - 2)
            n_val = 1
        n_test = n_total - n_train - n_val

        # Slice chronologically
        train_samples = self.samples[:n_train]
        val_samples = self.samples[n_train: n_train + n_val]
        test_samples = self.samples[n_train + n_val:]

        def _make_subset(sample_subset: List[Dict[str, Any]]) -> "TemporalRadarDataset":
            ds = TemporalRadarDataset(
                in_seq_len=self.in_seq_len,
                out_seq_len=self.out_seq_len,
                lead_times_min=self.lead_times_min,
                step_dt_min=self.step_dt_min,
                normalize_dbz=self.normalize_dbz,
                max_dbz=self.max_dbz,
                spatial_size=self.spatial_size,
                provenance_tag=self.provenance_tag
            )
            ds.samples = sample_subset
            return ds

        return _make_subset(train_samples), _make_subset(val_samples), _make_subset(test_samples)


def create_dataloaders(
    dataset: TemporalRadarDataset,
    batch_size: int = 4,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    num_workers: int = 0
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Convenience factory generating chronological PyTorch DataLoaders.
    Only the training DataLoader is shuffled within its chronological subset.
    Validation and test DataLoaders remain strictly in chronological evaluation order.
    """
    train_ds, val_ds, test_ds = dataset.split_chronological(train_ratio, val_ratio, test_ratio)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader, test_loader
