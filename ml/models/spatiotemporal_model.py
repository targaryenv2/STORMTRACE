#!/usr/bin/env python3
"""
STORMTRACE Genuine PyTorch Spatiotemporal Forecasting Model
================================================================================
Implements an authentic, trainable PyTorch Spatiotemporal Convolutional-LSTM
(ConvLSTM) neural network for convective precipitation and radar nowcasting.

Mathematical Model:
    Given a sequence of T_in historical spatial fields X_{1:T_in} in R^{B x T_in x C_in x H x W},
    the encoder processes spatial features through convolutional encodings,
    recurrent ConvLSTM cells track spatial-temporal dynamics with learned gates
    (input, forget, output, candidate cell state), and a recurrent decoder
    generates T_out future spatial forecast horizons in R^{B x T_out x C_out x H x W}.

Gates Formulation:
    i_t = sigma(W_xi * X_t + W_hi * H_{t-1} + b_i)
    f_t = sigma(W_xf * X_t + W_hf * H_{t-1} + b_f)
    g_t = tanh(W_xg * X_t + W_hg * H_{t-1} + b_g)
    o_t = sigma(W_xo * X_t + W_ho * H_{t-1} + b_o)
    C_t = f_t (hadamard) C_{t-1} + i_t (hadamard) g_t
    H_t = o_t (hadamard) tanh(C_t)
================================================================================
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class ModelConfig:
    """Configuration hyperparameters for the Spatiotemporal ConvLSTM model."""
    in_channels: int = 1               # Input modalities (e.g. 1 for Radar Reflectivity dBZ, or N for multimodal)
    out_channels: int = 1              # Output fields per horizon (e.g. 1 for Reflectivity / Convective intensity)
    hidden_dims: List[int] = field(default_factory=lambda: [32, 64])  # Channels in ConvLSTM layers
    kernel_size: int = 3               # Spatial convolution kernel size
    num_layers: int = 2                # Number of recurrent ConvLSTM layers
    in_seq_len: int = 5                # Historical time steps (e.g. T-60, T-45, T-30, T-15, T0)
    out_seq_len: int = 6               # Future forecast horizons (+15, +30, +45, +60, +90, +120 min)
    lead_times_min: List[int] = field(default_factory=lambda: [15, 30, 45, 60, 90, 120])
    spatial_height: int = 64           # Spatial grid rows
    spatial_width: int = 64            # Spatial grid columns
    dropout_rate: float = 0.0          # Optional dropout probability
    activation: str = "leaky_relu"     # Encoder/Decoder non-linear activation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "in_channels": self.in_channels,
            "out_channels": self.out_channels,
            "hidden_dims": self.hidden_dims,
            "kernel_size": self.kernel_size,
            "num_layers": self.num_layers,
            "in_seq_len": self.in_seq_len,
            "out_seq_len": self.out_seq_len,
            "lead_times_min": self.lead_times_min,
            "spatial_height": self.spatial_height,
            "spatial_width": self.spatial_width,
            "dropout_rate": self.dropout_rate,
            "activation": self.activation,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModelConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ConvLSTMCell(nn.Module):
    """
    Genuine 2D Convolutional LSTM Cell with explicit gate computations.
    Computes learned spatial-recurrent transformations using 2D convolutions.
    """

    def __init__(self, in_channels: int, hidden_dim: int, kernel_size: int = 3, bias: bool = True):
        super().__init__()
        self.in_channels = in_channels
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        self.bias = bias

        # Joint 2D convolution for input, forget, cell candidate, and output gates (4 * hidden_dim)
        self.conv = nn.Conv2d(
            in_channels=self.in_channels + self.hidden_dim,
            out_channels=4 * self.hidden_dim,
            kernel_size=self.kernel_size,
            padding=self.padding,
            bias=self.bias
        )

        # Initialize weights with standard Xavier / orthogonal distributions
        self._init_weights()

    def _init_weights(self):
        nn.init.xavier_uniform_(self.conv.weight)
        if self.bias and self.conv.bias is not None:
            # Initialize forget gate bias to 1.0 to encourage gradient flow initially
            nn.init.zeros_(self.conv.bias)
            self.conv.bias.data[self.hidden_dim: 2 * self.hidden_dim].fill_(1.0)

    def forward(
        self,
        x: torch.Tensor,
        hx: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for a single time step.
        Args:
            x: Input tensor of shape [B, in_channels, H, W]
            hx: Tuple of (hidden_state, cell_state), each of shape [B, hidden_dim, H, W]
        Returns:
            (h_next, c_next): Updated hidden and cell states
        """
        batch_size, _, height, width = x.size()

        if hx is None:
            h_prev = torch.zeros(batch_size, self.hidden_dim, height, width, device=x.device, dtype=x.dtype)
            c_prev = torch.zeros(batch_size, self.hidden_dim, height, width, device=x.device, dtype=x.dtype)
        else:
            h_prev, c_prev = hx

        # Concatenate along channel dimension: [B, in_channels + hidden_dim, H, W]
        combined = torch.cat([x, h_prev], dim=1)
        gates = self.conv(combined)

        # Split gates: i (input), f (forget), g (candidate), o (output)
        i_gate, f_gate, g_gate, o_gate = torch.chunk(gates, 4, dim=1)

        i = torch.sigmoid(i_gate)
        f = torch.sigmoid(f_gate)
        g = torch.tanh(g_gate)
        o = torch.sigmoid(o_gate)

        c_next = f * c_prev + i * g
        h_next = o * torch.tanh(c_next)

        return h_next, c_next


class ConvLSTM(nn.Module):
    """
    Multi-layer Convolutional LSTM recurrent sequence processor.
    Handles temporal sequence inputs [B, T, C, H, W].
    """

    def __init__(
        self,
        in_channels: int,
        hidden_dims: List[int],
        kernel_size: int = 3,
        num_layers: int = 2,
        bias: bool = True
    ):
        super().__init__()
        self.in_channels = in_channels
        self.hidden_dims = hidden_dims
        self.kernel_size = kernel_size
        self.num_layers = num_layers
        self.bias = bias

        cells = []
        for i in range(self.num_layers):
            cur_in = self.in_channels if i == 0 else self.hidden_dims[i - 1]
            cells.append(ConvLSTMCell(cur_in, self.hidden_dims[i], kernel_size=self.kernel_size, bias=self.bias))
        self.cells = nn.ModuleList(cells)

    def forward(
        self,
        x_seq: torch.Tensor,
        hidden_states: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None
    ) -> Tuple[torch.Tensor, List[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Args:
            x_seq: Input temporal tensor [B, T, C, H, W]
            hidden_states: Optional list of (h, c) for each layer
        Returns:
            layer_outputs: Sequence output of last layer [B, T, hidden_dims[-1], H, W]
            last_states: List of final (h, c) tuples for all layers
        """
        batch_size, seq_len, _, height, width = x_seq.size()

        if hidden_states is None:
            hidden_states = [None] * self.num_layers

        cur_layer_input = x_seq
        last_states = []

        for layer_idx, cell in enumerate(self.cells):
            h, c = (
                (None, None)
                if hidden_states[layer_idx] is None
                else hidden_states[layer_idx]
            )
            layer_output_list = []

            for t in range(seq_len):
                x_t = cur_layer_input[:, t, :, :, :]
                hx = (h, c) if h is not None else None
                h, c = cell(x_t, hx)
                layer_output_list.append(h)

            cur_layer_input = torch.stack(layer_output_list, dim=1)
            last_states.append((h, c))

        return cur_layer_input, last_states


class SpatiotemporalForecastNet(nn.Module):
    """
    STORMTRACE Spatiotemporal Convolutional-LSTM Forecasting Neural Network.
    
    Architecture:
        1. Spatial Feature Encoder: Conv2D layers extracting spatial patterns
        2. Recurrent ConvLSTM Core: Tracks convective temporal evolution
        3. Autoregressive / Multi-Horizon Forecaster: Extrapolates future horizons
        4. Spatial Output Projection Head: Produces target forecast channels
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        super().__init__()
        self.config = config or ModelConfig()

        # 1. Spatial Encoder
        encoder_channels = self.config.hidden_dims[0]
        drop_p = self.config.dropout_rate
        self.dropout = nn.Dropout2d(p=drop_p) if drop_p > 0 else nn.Identity()

        self.encoder = nn.Sequential(
            nn.Conv2d(self.config.in_channels, encoder_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(encoder_channels),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Dropout2d(p=drop_p) if drop_p > 0 else nn.Identity(),
            nn.Conv2d(encoder_channels, encoder_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(encoder_channels),
            nn.LeakyReLU(0.1, inplace=True)
        )

        # 2. Recurrent Encoder ConvLSTM
        self.convlstm = ConvLSTM(
            in_channels=encoder_channels,
            hidden_dims=self.config.hidden_dims,
            kernel_size=self.config.kernel_size,
            num_layers=self.config.num_layers
        )

        # 3. Forecaster Recurrent Core (Decoder ConvLSTM)
        forecaster_hidden = self.config.hidden_dims[-1]
        self.forecaster_cell = ConvLSTMCell(
            in_channels=forecaster_hidden,
            hidden_dim=forecaster_hidden,
            kernel_size=self.config.kernel_size
        )

        # 4. Spatial Decoder / Output Projection Head
        self.decoder = nn.Sequential(
            nn.Conv2d(forecaster_hidden, encoder_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(encoder_channels),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Dropout2d(p=drop_p) if drop_p > 0 else nn.Identity(),
            nn.Conv2d(encoder_channels, self.config.out_channels, kernel_size=1)
        )

    @property
    def total_parameters(self) -> int:
        """Returns the total number of parameters in the model."""
        return sum(p.numel() for p in self.parameters())

    @property
    def trainable_parameters(self) -> int:
        """Returns the number of trainable (grad-enabled) parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    @property
    def non_trainable_parameters(self) -> int:
        """Returns the number of frozen / non-trainable parameters."""
        return sum(p.numel() for p in self.parameters() if not p.requires_grad)

    def forward(
        self,
        x_seq: torch.Tensor,
        future_steps: Optional[int] = None
    ) -> torch.Tensor:
        """
        Forward prediction across future forecast horizons.
        
        Args:
            x_seq: Historical input tensor of shape [B, T_in, C_in, H, W]
            future_steps: Number of forecast horizons to produce (defaults to config.out_seq_len)
            
        Returns:
            Forecast tensor of shape [B, T_out, C_out, H, W]
        """
        if x_seq.dim() != 5:
            raise ValueError(
                f"Expected 5D input tensor [Batch, Time, Channels, Height, Width], got shape {list(x_seq.shape)}"
            )

        batch_size, in_time, channels, height, width = x_seq.size()
        out_time = future_steps or self.config.out_seq_len

        # Step 1: Spatial Feature Encoding across time steps
        encoded_frames = []
        for t in range(in_time):
            frame = x_seq[:, t, :, :, :]  # [B, C_in, H, W]
            feat = self.encoder(frame)     # [B, encoder_channels, H, W]
            encoded_frames.append(feat)
        encoded_seq = torch.stack(encoded_frames, dim=1)  # [B, T_in, encoder_channels, H, W]

        # Step 2: Temporal Encoding with ConvLSTM
        _, states = self.convlstm(encoded_seq)

        # Step 3: Autoregressive Future Horizons Forecasting
        last_h, last_c = states[-1]  # Top layer hidden and cell states
        cur_input = last_h
        cur_state = (last_h, last_c)

        forecast_frames = []
        for step in range(out_time):
            next_h, next_c = self.forecaster_cell(cur_input, cur_state)
            cur_state = (next_h, next_c)

            # Project hidden state to output channels (e.g. reflectivity / probability field)
            out_frame = self.decoder(next_h)
            forecast_frames.append(out_frame)

            # Feedback top representation for next autoregressive horizon
            cur_input = next_h

        # Output shape: [B, T_out, C_out, H, W]
        forecast_tensor = torch.stack(forecast_frames, dim=1)
        return forecast_tensor

    def predict_mc_dropout(
        self,
        x_seq: torch.Tensor,
        future_steps: Optional[int] = None,
        num_passes: int = 25
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Executes genuine Monte Carlo Dropout inference by running multiple stochastic forward passes.
        
        Args:
            x_seq: Input tensor [B, T_in, C_in, H, W]
            future_steps: Number of forecast horizons
            num_passes: Number of stochastic MC passes (default 25)
            
        Returns:
            (mean_forecast, epistemic_uncertainty_std):
                mean_forecast: Expected forecast tensor [B, T_out, C_out, H, W]
                epistemic_uncertainty_std: Predictive standard deviation [B, T_out, C_out, H, W]
        """
        was_training = self.training
        # Force dropout layers to active training mode for stochastic sampling
        self.train()

        passes = []
        with torch.no_grad():
            for _ in range(num_passes):
                pred = self.forward(x_seq, future_steps=future_steps)
                passes.append(pred)

        # Restore original train/eval mode
        if not was_training:
            self.eval()

        # Stack shape: [num_passes, B, T_out, C_out, H, W]
        stacked = torch.stack(passes, dim=0)
        mean_forecast = torch.mean(stacked, dim=0)
        epistemic_uncertainty_std = torch.std(stacked, dim=0)

        return mean_forecast, epistemic_uncertainty_std

    def save_checkpoint(
        self,
        filepath: str,
        optimizer: Optional[torch.optim.Optimizer] = None,
        epoch: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Saves a clean PyTorch checkpoint dictionary."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        checkpoint = {
            "model_architecture": "StormTrace_ConvLSTM_ForecastNet",
            "model_config": self.config.to_dict(),
            "model_state_dict": self.state_dict(),
            "trainable_parameters": self.trainable_parameters,
            "total_parameters": self.total_parameters,
        }
        if optimizer is not None:
            checkpoint["optimizer_state_dict"] = optimizer.state_dict()
        if epoch is not None:
            checkpoint["epoch"] = epoch
        if extra_metadata is not None:
            checkpoint["metadata"] = extra_metadata

        torch.save(checkpoint, filepath)
        return filepath

    @classmethod
    def load_checkpoint(
        cls,
        filepath: str,
        map_location: Union[str, torch.device] = "cpu"
    ) -> Tuple["SpatiotemporalForecastNet", Dict[str, Any]]:
        """Loads a model instance from a PyTorch checkpoint."""
        checkpoint = torch.load(filepath, map_location=map_location, weights_only=False)
        config_dict = checkpoint.get("model_config", {})
        config = ModelConfig.from_dict(config_dict)
        model = cls(config)
        model.load_state_dict(checkpoint["model_state_dict"])
        return model, checkpoint


# Clean class alias for STORMTRACE
StormTraceConvLSTMNet = SpatiotemporalForecastNet
