#!/usr/bin/env python3
"""
STORMTRACE Multimodal Spatiotemporal Deep Learning Model
================================================================================
Implements genuine Multimodal Deep Neural Fusion for Spatiotemporal Convective Nowcasting.
Fuses heterogeneous weather modalities with dynamic availability masking:
    1. Radar Reflectivity (dBZ)
    2. Satellite Infrared Brightness Temperature (INSAT-3DS TIR1/TIR2)
    3. NWP Reanalysis Thermodynamics (ERA5 CAPE & Vertical Wind Shear)
    4. Satellite Precipitation (NASA GPM IMERG)
    5. Lightning Climatological Density (WGLC Baseline)

Architecture:
    Modality Encoders -> Dynamic Gated Fusion -> Recurrent ConvLSTM -> Forecaster -> Multi-Horizon Output
================================================================================
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import torch
import torch.nn as nn
import torch.nn.functional as F

from .spatiotemporal_model import ConvLSTM, ConvLSTMCell, ModelConfig


class ModalityFeatureEncoder(nn.Module):
    """Encodes single channel/spatial field into latent feature representations."""

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=kernel_size // 2),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size, padding=kernel_size // 2),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.1, inplace=True)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DynamicModalityGating(nn.Module):
    """
    Learned attention-based fusion layer with strict missing-modality gating.
    Applies availability mask to guarantee missing sensors contribute zero weight.
    """

    def __init__(self, feature_dims: List[int], fused_dim: int = 64):
        super().__init__()
        self.feature_dims = feature_dims
        self.total_dim = sum(feature_dims)
        self.fused_dim = fused_dim

        # Channel-wise feature transformation
        self.gate_conv = nn.Sequential(
            nn.Conv2d(self.total_dim, fused_dim, kernel_size=1),
            nn.BatchNorm2d(fused_dim),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Conv2d(fused_dim, fused_dim, kernel_size=3, padding=1),
            nn.BatchNorm2d(fused_dim),
            nn.LeakyReLU(0.1, inplace=True)
        )

    def forward(
        self,
        modality_features: List[torch.Tensor],
        availability_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            modality_features: List of tensors, each [B, C_i, H, W]
            availability_mask: Optional binary tensor [B, num_modalities] (1 = available, 0 = missing)
        Returns:
            fused_tensor: [B, fused_dim, H, W]
        """
        masked_features = []
        for idx, feat in enumerate(modality_features):
            if availability_mask is not None:
                # Mask tensor shaped [B, 1, 1, 1]
                m = availability_mask[:, idx].view(-1, 1, 1, 1)
                masked_feat = feat * m
            else:
                masked_feat = feat
            masked_features.append(masked_feat)

        combined = torch.cat(masked_features, dim=1) # [B, total_dim, H, W]
        fused = self.gate_conv(combined)              # [B, fused_dim, H, W]
        return fused


class MultimodalSpatiotemporalForecastNet(nn.Module):
    """
    STORMTRACE Multimodal ConvLSTM Forecasting Neural Network.
    
    Accepts multimodal temporal input dictionary:
        - radar: [B, T_in, 1, H, W]
        - satellite: [B, T_in, 1, H, W]
        - nwp: [B, T_in, 2, H, W]
        - imerg: [B, T_in, 1, H, W]
        - lightning: [B, T_in, 1, H, W]
        - availability_mask: [B, 5]
    """

    def __init__(
        self,
        out_channels: int = 1,
        hidden_dims: Optional[List[int]] = None,
        out_seq_len: int = 6,
        dropout_rate: float = 0.2
    ):
        super().__init__()
        self.hidden_dims = hidden_dims or [32, 64]
        self.out_seq_len = out_seq_len
        self.dropout_rate = dropout_rate

        # 1. Modality-specific encoders
        self.radar_enc = ModalityFeatureEncoder(in_channels=1, out_channels=32)
        self.sat_enc = ModalityFeatureEncoder(in_channels=1, out_channels=16)
        self.nwp_enc = ModalityFeatureEncoder(in_channels=2, out_channels=16)
        self.imerg_enc = ModalityFeatureEncoder(in_channels=1, out_channels=16)
        self.lgt_enc = ModalityFeatureEncoder(in_channels=1, out_channels=16)

        # 2. Dynamic Gating Fusion (32 + 16 + 16 + 16 + 16 = 96 -> 32)
        self.fusion = DynamicModalityGating(
            feature_dims=[32, 16, 16, 16, 16],
            fused_dim=self.hidden_dims[0]
        )

        # 3. Recurrent ConvLSTM Core
        self.convlstm = ConvLSTM(
            in_channels=self.hidden_dims[0],
            hidden_dims=self.hidden_dims,
            kernel_size=3,
            num_layers=len(self.hidden_dims)
        )

        # 4. Forecaster Recurrent Core
        forecaster_hidden = self.hidden_dims[-1]
        self.forecaster_cell = ConvLSTMCell(
            in_channels=forecaster_hidden,
            hidden_dim=forecaster_hidden,
            kernel_size=3
        )

        # 5. Output Projection Head (Radar Reflectivity / Convective Storms)
        self.decoder = nn.Sequential(
            nn.Conv2d(forecaster_hidden, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Dropout2d(p=self.dropout_rate) if self.dropout_rate > 0 else nn.Identity(),
            nn.Conv2d(32, out_channels, kernel_size=1)
        )

        # 6. Dedicated Lightning Flash Density & Strike Probability Head
        self.lightning_head = nn.Sequential(
            nn.Conv2d(forecaster_hidden, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Conv2d(32, 16, kernel_size=3, padding=1),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Conv2d(16, 1, kernel_size=1),
            nn.Sigmoid() # Calibrated lightning strike probability in [0.0, 1.0]
        )

    @property
    def trainable_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def forward(
        self,
        multimodal_inputs: Dict[str, torch.Tensor],
        future_steps: Optional[int] = None,
        return_dict: bool = False
    ) -> Union[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Forward pass for multimodal sequence.
        
        Args:
            multimodal_inputs: Dictionary containing input tensors.
            future_steps: Number of forecast frames to roll out (default: 6).
            return_dict: If True, returns dict with keys 'reflectivity' and 'lightning_prob'.
                         If False, returns reflectivity tensor for backward compatibility.
        """
        radar = multimodal_inputs["radar"] # [B, T, 1, H, W]
        b, t, _, h, w = radar.shape
        out_time = future_steps or self.out_seq_len

        satellite = multimodal_inputs.get("satellite", torch.zeros_like(radar))
        nwp = multimodal_inputs.get("nwp", torch.zeros(b, t, 2, h, w, device=radar.device, dtype=radar.dtype))
        imerg = multimodal_inputs.get("imerg", torch.zeros_like(radar))
        lightning = multimodal_inputs.get("lightning", torch.zeros_like(radar))
        mask = multimodal_inputs.get("availability_mask", None)

        # Encode & Fuse each time step
        fused_sequence = []
        for step in range(t):
            r_feat = self.radar_enc(radar[:, step])
            s_feat = self.sat_enc(satellite[:, step])
            n_feat = self.nwp_enc(nwp[:, step])
            i_feat = self.imerg_enc(imerg[:, step])
            l_feat = self.lgt_enc(lightning[:, step])

            fused_t = self.fusion([r_feat, s_feat, n_feat, i_feat, l_feat], availability_mask=mask)
            fused_sequence.append(fused_t)

        fused_seq_tensor = torch.stack(fused_sequence, dim=1) # [B, T, 32, H, W]

        # ConvLSTM Spatiotemporal Processing
        _, states = self.convlstm(fused_seq_tensor)

        last_h, last_c = states[-1]
        cur_input = last_h
        cur_state = (last_h, last_c)

        forecast_frames = []
        lightning_frames = []
        for _ in range(out_time):
            next_h, next_c = self.forecaster_cell(cur_input, cur_state)
            cur_state = (next_h, next_c)
            
            # Predict Reflectivity
            out_frame = self.decoder(next_h)
            forecast_frames.append(out_frame)
            
            # Predict Lightning Probability
            lgt_frame = self.lightning_head(next_h)
            lightning_frames.append(lgt_frame)
            
            cur_input = next_h

        refl_tensor = torch.stack(forecast_frames, dim=1) # [B, out_time, out_channels, H, W]
        lgt_tensor = torch.stack(lightning_frames, dim=1)   # [B, out_time, 1, H, W]

        if return_dict:
            return {
                "reflectivity": refl_tensor,
                "lightning_prob": lgt_tensor
            }
        return refl_tensor

    def predict_nowcast_and_lightning(
        self,
        multimodal_inputs: Dict[str, torch.Tensor],
        future_steps: Optional[int] = None
    ) -> Dict[str, torch.Tensor]:
        """Convenience method returning both reflectivity and lightning forecasts."""
        return self.forward(multimodal_inputs, future_steps=future_steps, return_dict=True)
