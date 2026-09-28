#!/usr/bin/env python3
"""
STORMTRACE Synthetic Storm Sequence Generator
Part 1: Generates realistic multi-channel convective storm sequences
(Radar Reflectivity dBZ, Satellite IR Cloud-Top Temp, Lightning Flash Density, CAPE)
with realistic physical lifecycles, advection kinematics, and split/merge events.
"""

import math
import random
import json
import time
from typing import List, Dict, Any, Tuple, Optional


class SyntheticCell:
    """Represents a single convective storm cell modeled as an anisotropic 2D Gaussian blob."""
    
    def __init__(
        self,
        cell_id: str,
        x: float,
        y: float,
        peak_dbz: float = 45.0,
        sigma_x: float = 6.0,
        sigma_y: float = 4.0,
        theta_rad: float = 0.4,
        vx: float = 1.2,
        vy: float = -0.4,
        lifecycle_duration: int = 18,
        region_name: str = "Central Domain"
    ):
        self.cell_id = cell_id
        self.x = x
        self.y = y
        self.base_peak_dbz = peak_dbz
        self.current_dbz = peak_dbz
        self.sigma_x = sigma_x
        self.sigma_y = sigma_y
        self.theta_rad = theta_rad
        self.vx = vx
        self.vy = vy
        self.age = 0
        self.lifecycle_duration = lifecycle_duration
        self.region_name = region_name
        self.is_split = False
        self.is_merged = False
        self.is_active = True
        self.history = []

    def update(self, allow_split: bool = True, allow_merge: bool = True, step_index: int = 0) -> Optional['SyntheticCell']:
        """Advance cell state by one 5-minute timestep."""
        if not self.is_active:
            return None

        self.age += 1
        self.history.append((self.x, self.y, self.current_dbz))

        # Advection with physical kinematic jitter
        jitter_x = (random.random() - 0.5) * 0.3
        jitter_y = (random.random() - 0.5) * 0.2
        self.x += self.vx + jitter_x
        self.y += self.vy + jitter_y

        # Lifecycle intensity curve: Growth -> Peak -> Dissipation
        norm_age = self.age / max(1, self.lifecycle_duration)
        if norm_age < 0.35:
            # Convective initiation & rapid intensification
            factor = 0.5 + (norm_age / 0.35) * 0.5
            self.current_dbz = self.base_peak_dbz * factor
            self.sigma_x *= 1.03
            self.sigma_y *= 1.02
        elif norm_age < 0.70:
            # Mature supercell stage
            factor = 1.0 + (random.random() - 0.5) * 0.05
            self.current_dbz = min(68.0, self.base_peak_dbz * factor)
        else:
            # Dissipation & stratiform decay
            decay_progress = (norm_age - 0.70) / 0.30
            factor = max(0.2, 1.0 - decay_progress * 0.75)
            self.current_dbz = self.base_peak_dbz * factor
            self.sigma_x *= 1.04  # Anvil dispersion
            self.sigma_y *= 1.03

        if norm_age >= 1.05 or self.current_dbz < 18.0:
            self.is_active = False

        # Occasional split event at peak maturity
        if allow_split and 4 <= self.age <= 8 and not self.is_split and random.random() < 0.18:
            self.is_split = True
            child_cell = SyntheticCell(
                cell_id=f"{self.cell_id}-B",
                x=self.x + 3.0,
                y=self.y + 2.0,
                peak_dbz=self.current_dbz * 0.85,
                sigma_x=self.sigma_x * 0.75,
                sigma_y=self.sigma_y * 0.75,
                theta_rad=self.theta_rad + 0.3,
                vx=self.vx * 0.9 + 0.6,
                vy=self.vy * 0.9 - 0.5,
                lifecycle_duration=max(8, self.lifecycle_duration - self.age),
                region_name=self.region_name
            )
            child_cell.is_split = True
            return child_cell

        return None

    def evaluate_point(self, grid_x: float, grid_y: float) -> float:
        """Evaluate anisotropic 2D Gaussian value at a specific grid coordinate."""
        dx = grid_x - self.x
        dy = grid_y - self.y

        # Rotate coordinates
        cos_t = math.cos(self.theta_rad)
        sin_t = math.sin(self.theta_rad)
        x_rot = dx * cos_t + dy * sin_t
        y_rot = -dx * sin_t + dy * cos_t

        sx2 = max(0.5, 2.0 * (self.sigma_x ** 2))
        sy2 = max(0.5, 2.0 * (self.sigma_y ** 2))

        exponent = -((x_rot ** 2) / sx2 + (y_rot ** 2) / sy2)
        if exponent < -9.0:
            return 0.0
        return self.current_dbz * math.exp(exponent)


class SyntheticStormGenerator:
    """Generates standardized multi-frame multi-channel meteorological sequences."""

    SCENARIO_CONFIGS = {
        "single_developing_storm": {
            "name": "Single Developing Supercell",
            "description": "Rapid convective initiation over high-terrain plateau intensifying into an isolated supercell with peak reflectivity above 60 dBZ.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 14.0, "y": 20.0, "peak_dbz": 62.0, "sigma_x": 5.5, "sigma_y": 4.0, "vx": 1.2, "vy": -0.2, "duration": 28, "region": "Chota Nagpur / Ranchi"}
            ]
        },
        "multiple_storms_merging": {
            "name": "Multiple Storms Merging into Squall Line",
            "description": "Two adjacent pre-frontal convective clusters traveling eastward that merge at t=+35m into an intense squall line.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 12.0, "y": 18.0, "peak_dbz": 54.0, "sigma_x": 5.0, "sigma_y": 3.5, "vx": 1.3, "vy": 0.2, "duration": 28, "region": "Gangetic Bengal"},
                {"x": 14.0, "y": 30.0, "peak_dbz": 58.0, "sigma_x": 6.0, "sigma_y": 4.5, "vx": 1.1, "vy": -0.4, "duration": 28, "region": "Kolkata Coastal Corridor"}
            ]
        },
        "storm_splitting_near_airport": {
            "name": "Supercell Splitting near Terminal Airport",
            "description": "Severe convective updraft undergoing storm bisection (left-mover and right-mover cells) within 15 km of terminal airspace.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 18.0, "y": 24.0, "peak_dbz": 64.0, "sigma_x": 7.0, "sigma_y": 5.0, "vx": 1.0, "vy": -0.2, "duration": 28, "region": "Chennai MAA Terminal Airspace"}
            ]
        },
        "weakening_dissipating_storm": {
            "name": "Weakening Multicell Cluster",
            "description": "Decaying evening thunderstorm cluster transitioning from active convective cores to diffuse stratiform precipitation.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 24.0, "y": 22.0, "peak_dbz": 48.0, "sigma_x": 8.0, "sigma_y": 6.0, "vx": 0.8, "vy": -0.3, "duration": 28, "region": "Western Ghats / Malabar"}
            ]
        },
        "global_tropical_cyclone_band": {
            "name": "Global Tropical Convective Band",
            "description": "Intense tropical convective rainband with high lightning density modeled over equatorial maritime domains.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 12.0, "y": 15.0, "peak_dbz": 59.0, "sigma_x": 7.5, "sigma_y": 4.5, "vx": 1.2, "vy": 0.3, "duration": 28, "region": "São Paulo / South Atlantic"},
                {"x": 22.0, "y": 22.0, "peak_dbz": 55.0, "sigma_x": 6.0, "sigma_y": 4.0, "vx": 0.9, "vy": 0.1, "duration": 28, "region": "Amazon Basin (Manaus)"}
            ]
        },
        "remal_outer_squall_band": {
            "name": "Cyclone Remal Outer Convective Rainband",
            "description": "Severe spiral outer rainband tracking northward toward West Bengal / Sundarbans with extreme shear and rain rates.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 20.0, "y": 12.0, "peak_dbz": 61.0, "sigma_x": 8.0, "sigma_y": 3.8, "vx": 0.8, "vy": 1.1, "duration": 28, "region": "North Bay of Bengal / Sundarbans"},
                {"x": 28.0, "y": 18.0, "peak_dbz": 56.0, "sigma_x": 6.5, "sigma_y": 4.2, "vx": 0.9, "vy": 0.9, "duration": 28, "region": "Dhamra / Coastal Odisha"}
            ]
        },
        "kalbaishakhi_norwester_squall": {
            "name": "Severe Kalbaishakhi Nor'wester Squall Line",
            "description": "Deep pre-monsoon convective squall line initiating over Ranchi plateau propagating rapidly southeast into Kolkata.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 10.0, "y": 20.0, "peak_dbz": 63.0, "sigma_x": 9.0, "sigma_y": 3.5, "vx": 1.6, "vy": -0.6, "duration": 28, "region": "Ranchi - Kharagpur Corridor"}
            ]
        },
        "yaas_prelandfall_surge": {
            "name": "Cyclone Yaas Pre-Landfall Convective Surge",
            "description": "Intense spiral rainbands with embedded microbursts advancing onto the Balasore-Digha coastline.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 16.0, "y": 14.0, "peak_dbz": 58.0, "sigma_x": 6.8, "sigma_y": 4.8, "vx": 1.1, "vy": 0.7, "duration": 28, "region": "Balasore / Digha Coast"}
            ]
        },
        "chota_nagpur_high_cape_supercell": {
            "name": "Chota Nagpur Plateau High-CAPE Supercell",
            "description": "Explosive diurnal heating supercell over complex topography with high CAPE (>3200 J/kg) and severe hail signature.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 18.0, "y": 26.0, "peak_dbz": 65.0, "sigma_x": 5.0, "sigma_y": 4.5, "vx": 1.0, "vy": -0.1, "duration": 28, "region": "Jamshedpur / Dhanbad Plateau"}
            ]
        },
        "odisha_coastal_multicell": {
            "name": "Odisha Coastal Sea-Breeze Multicell",
            "description": "Sea-breeze frontal convergence triggering a series of multicellular thunderstorms along the Bhubaneswar-Puri axis.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 22.0, "y": 16.0, "peak_dbz": 53.0, "sigma_x": 6.0, "sigma_y": 4.0, "vx": 0.7, "vy": 0.6, "duration": 28, "region": "Bhubaneswar Coastal Axis"}
            ]
        },
        "monsoon_trough_convective_depression": {
            "name": "Monsoon Trough Depression Cluster",
            "description": "Widespread monsoon low-pressure convective clusters producing continuous moderate-to-heavy convective precipitation.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 15.0, "y": 22.0, "peak_dbz": 51.0, "sigma_x": 10.0, "sigma_y": 7.0, "vx": 0.9, "vy": 0.2, "duration": 28, "region": "Gangetic Basin"}
            ]
        },
        "western_ghats_orographic_burst": {
            "name": "Western Ghats Orographic Convective Burst",
            "description": "Deep maritime moisture forced over mountain escarpment generating anchored torrential convective rain cells.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 12.0, "y": 28.0, "peak_dbz": 57.0, "sigma_x": 5.8, "sigma_y": 5.2, "vx": 0.6, "vy": 0.1, "duration": 28, "region": "Malabar Mountain Slopes"}
            ]
        },
        "gangetic_plains_derecho": {
            "name": "Gangetic Plains Fast-Moving Derecho",
            "description": "Long-lived convective system with a prominent bow echo and destructive straight-line winds sweeping eastward.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 8.0, "y": 22.0, "peak_dbz": 62.0, "sigma_x": 11.0, "sigma_y": 3.2, "vx": 1.8, "vy": -0.4, "duration": 28, "region": "Bihar - West Bengal Corridor"}
            ]
        },
        "brahmaputra_valley_mcs": {
            "name": "Brahmaputra Valley Nocturnal MCS",
            "description": "Nighttime mesoscale convective complex trapped in the river valley with extensive anvil canopy and continuous lightning.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 25.0, "y": 32.0, "peak_dbz": 56.0, "sigma_x": 8.5, "sigma_y": 5.5, "vx": 0.7, "vy": -0.2, "duration": 28, "region": "Assam / Brahmaputra Basin"}
            ]
        },
        "subtropical_jet_divergence_squall": {
            "name": "Subtropical Jet Divergence Squall Complex",
            "description": "Upper-level divergence coupled with low-level moisture convergence driving widespread multi-cluster thunderstorm outbreaks.",
            "duration_steps": 30,
            "initial_cells": [
                {"x": 14.0, "y": 25.0, "peak_dbz": 60.0, "sigma_x": 7.2, "sigma_y": 4.8, "vx": 1.4, "vy": 0.1, "duration": 28, "region": "Jharkhand - Bengal Border"}
            ]
        }
    }

    def __init__(self, grid_width: int = 64, grid_height: int = 64, time_step_min: int = 5):
        self.width = grid_width
        self.height = grid_height
        self.dt_min = time_step_min

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Return available synthetic scenario templates."""
        scenarios = []
        for key, conf in self.SCENARIO_CONFIGS.items():
            scenarios.append({
                "id": key,
                "name": conf["name"],
                "description": conf["description"],
                "duration_steps": conf["duration_steps"],
                "duration_min": conf["duration_steps"] * self.dt_min
            })
        return scenarios

    def generate_sequence(self, scenario_id: str = "single_developing_storm", seed: Optional[int] = 42) -> Dict[str, Any]:
        """
        Generate complete time-series storm sequence for a scenario.
        Returns JSON-serializable structured sequence matching pipeline tensor shape.
        """
        if seed is not None:
            random.seed(seed)

        config = self.SCENARIO_CONFIGS.get(scenario_id, self.SCENARIO_CONFIGS["single_developing_storm"])
        num_steps = config["duration_steps"]

        # Initialize synthetic cells
        active_cells: List[SyntheticCell] = []
        for i, c_cfg in enumerate(config["initial_cells"]):
            cell = SyntheticCell(
                cell_id=f"SYN-{scenario_id[:4].upper()}-{i+1:02d}",
                x=c_cfg["x"],
                y=c_cfg["y"],
                peak_dbz=c_cfg["peak_dbz"],
                sigma_x=c_cfg["sigma_x"],
                sigma_y=c_cfg["sigma_y"],
                vx=c_cfg["vx"],
                vy=c_cfg["vy"],
                lifecycle_duration=c_cfg["duration"],
                region_name=c_cfg.get("region", "Operational Core")
            )
            active_cells.append(cell)

        frames = []
        base_timestamp = int(time.time()) - (num_steps * self.dt_min * 60)

        for step in range(num_steps):
            frame_time_min = step * self.dt_min
            step_events = []

            # Update existing cells and capture any newly spawned split cells
            new_spawned = []
            for cell in active_cells:
                child = cell.update(allow_split=True, step_index=step)
                if child:
                    new_spawned.append(child)
                    step_events.append({
                        "event_type": "CELL_SPLIT",
                        "parent_id": cell.cell_id,
                        "child_id": child.cell_id,
                        "message": f"Convective updraft split: {cell.cell_id} spawned {child.cell_id}"
                    })

            # Check for cell merge (distance < 5.0 units)
            merged_cells = []
            for i in range(len(active_cells)):
                for j in range(i + 1, len(active_cells)):
                    c1 = active_cells[i]
                    c2 = active_cells[j]
                    if c1.is_active and c2.is_active:
                        dist = math.hypot(c1.x - c2.x, c1.y - c2.y)
                        if dist < 5.0 and step >= 4:
                            c1.is_merged = True
                            c1.base_peak_dbz = max(c1.current_dbz, c2.current_dbz) + 4.0
                            c1.sigma_x = max(c1.sigma_x, c2.sigma_x) * 1.2
                            c2.is_active = False
                            merged_cells.append(c2.cell_id)
                            step_events.append({
                                "event_type": "CELL_MERGE",
                                "dominant_id": c1.cell_id,
                                "absorbed_id": c2.cell_id,
                                "message": f"Convective clusters merged: {c1.cell_id} absorbed {c2.cell_id}"
                            })

            active_cells.extend(new_spawned)

            # Filter living cells
            living_cells = [c for c in active_cells if c.is_active]

            # Render 2D Multi-Modal Grids
            refl_grid, sat_grid, lgt_grid, cape_grid = self._render_modalities(living_cells, step)

            # Extract cell metadata list for downstream tracking
            cell_telemetry = []
            for c in living_cells:
                speed_kmh = round(math.hypot(c.vx, c.vy) * 32.0, 1)
                deg = round((math.degrees(math.atan2(c.vx, -c.vy)) + 360) % 360, 0)
                lgt_rate = int(max(0, (c.current_dbz - 35.0) * 28.0)) if c.current_dbz > 35 else 0
                
                # Warning level
                if c.current_dbz >= 55.0:
                    warn = "RED"
                elif c.current_dbz >= 45.0:
                    warn = "ORANGE"
                else:
                    warn = "YELLOW"

                cell_telemetry.append({
                    "cell_id": c.cell_id,
                    "location_name": f"{c.region_name} Cell",
                    "centroid_grid": [round(c.x, 2), round(c.y, 2)],
                    "max_dbz": round(c.current_dbz, 1),
                    "severity_score": int(min(100, (c.current_dbz / 65.0) * 100)),
                    "speed_kmh": speed_kmh,
                    "direction_deg": deg,
                    "lightning_rate": f"{lgt_rate}/h",
                    "warning_level": warn,
                    "is_split": c.is_split,
                    "is_merged": c.is_merged,
                    "age_min": c.age * self.dt_min
                })

            frames.append({
                "step_index": step,
                "time_min": frame_time_min,
                "timestamp_epoch": base_timestamp + (step * self.dt_min * 60),
                "active_cell_count": len(living_cells),
                "cells": cell_telemetry,
                "events": step_events,
                "grids": {
                    "reflectivity_dbz": refl_grid,
                    "satellite_ir_temp_c": sat_grid,
                    "lightning_flash_density": lgt_grid,
                    "cape_j_kg": cape_grid
                }
            })

        return {
            "status": "success",
            "data_source": "synthetic",
            "generator_version": "1.0.0",
            "scenario": {
                "id": scenario_id,
                "name": config["name"],
                "description": config["description"],
                "grid_resolution": f"{self.width}x{self.height}",
                "total_frames": num_steps,
                "time_step_minutes": self.dt_min,
                "total_duration_minutes": num_steps * self.dt_min
            },
            "frames": frames
        }

    def _render_modalities(self, cells: List[SyntheticCell], step: int) -> Tuple[List[List[float]], List[List[float]], List[List[float]], List[List[float]]]:
        """Render the 4 synchronized synthetic meteorological channels."""
        refl = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        sat = [[-22.0 for _ in range(self.width)] for _ in range(self.height)]
        lgt = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        cape = [[1800.0 + (random.random() - 0.5) * 80.0 for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                # 1. Radar Reflectivity: Max over active Gaussian blobs + sensor noise
                max_val = 0.0
                for c in cells:
                    v = c.evaluate_point(float(x), float(y))
                    if v > max_val:
                        max_val = v
                
                # Add slight Gaussian sensor noise (clipped to 0)
                noise = (random.random() - 0.5) * 1.5 if max_val > 5.0 else 0.0
                refl_val = max(0.0, min(75.0, round(max_val + noise, 1)))
                refl[y][x] = refl_val

                # 2. Satellite IR Cloud-Top Temperature (°C): Inversely correlated with storm height
                if refl_val > 15.0:
                    ir_temp = -25.0 - ((refl_val - 15.0) / 50.0) * 52.0
                    sat[y][x] = round(ir_temp + (random.random() - 0.5) * 1.2, 1)
                else:
                    sat[y][x] = round(-20.0 + (random.random() - 0.5) * 2.0, 1)

                # 3. Lightning Activity: Probabilistically sampled flash density in core (dBZ > 40)
                if refl_val >= 40.0:
                    prob = (refl_val - 40.0) / 25.0
                    if random.random() < prob:
                        flash_density = round(prob * 14.0 + random.random() * 4.0, 1)
                        lgt[y][x] = flash_density

                # 4. CAPE (J/kg): Elevated instability in vicinity of convective development
                if refl_val > 10.0:
                    cape_val = 2200.0 + (refl_val / 65.0) * 1800.0
                    cape[y][x] = round(cape_val + (random.random() - 0.5) * 120.0, 0)

        return refl, sat, lgt, cape
