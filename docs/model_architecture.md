# STORMTRACE Spatiotemporal Deep Learning Model Architecture

## 1. Overview
**Model Name**: `StormTraceConvLSTMNet` / `SpatiotemporalForecastNet`  
**Framework**: PyTorch (`torch.nn.Module`)  
**Task**: Spatiotemporal Convective Weather Forecasting & Radar Nowcasting  
**Implementation Type**: Deep Neural Network with genuine 2D Convolutional LSTM gating mechanisms and autoregressive multi-horizon forecasting.

---

## 2. Spatiotemporal Formulation & Gating Equations

For each recurrent time step $t$, the input spatial feature map $X_t \in \mathbb{R}^{B \times C_{in} \times H \times W}$ and previous hidden state $H_{t-1} \in \mathbb{R}^{B \times C_{hid} \times H \times W}$ are transformed via 2D spatial convolutions across four distinct gates:

$$\begin{aligned}
i_t &= \sigma(W_{xi} * X_t + W_{hi} * H_{t-1} + b_i) \quad &\text{(Input Gate)} \\
f_t &= \sigma(W_{xf} * X_t + W_{hf} * H_{t-1} + b_f) \quad &\text{(Forget Gate)} \\
g_t &= \tanh(W_{xg} * X_t + W_{hg} * H_{t-1} + b_g) \quad &\text{(Candidate Cell State)} \\
o_t &= \sigma(W_{xo} * X_t + W_{ho} * H_{t-1} + b_o) \quad &\text{(Output Gate)} \\
C_t &= f_t \odot C_{t-1} + i_t \odot g_t \quad &\text{(Cell State Memory Update)} \\
H_t &= o_t \odot \tanh(C_t) \quad &\text{(Hidden State Output)}
\end{aligned}$$

where $*$ denotes 2D spatial convolution and $\odot$ represents the Hadamard element-wise product.

---

## 3. Tensor Contract

### Input Tensor Contract
- **Shape**: `[B, T_in, C_in, H, W]`
- **Default Dimensions**: `[Batch Size, 5, 1, 64, 64]`
  - `B`: Batch size (e.g. 1 to 32)
  - `T_in = 5`: Historical observation frames ($T-60, T-45, T-30, T-15, T0$)
  - `C_in = 1`: Primary radar reflectivity channel (extensible to multimodal $C_{in} = 5$)
  - `H = 64, W = 64`: Spatial grid height and width matching STORMTRACE regional domain

### Output Tensor Contract
- **Shape**: `[B, T_out, C_out, H, W]`
- **Default Dimensions**: `[Batch Size, 6, 1, 64, 64]`
  - `B`: Batch size
  - `T_out = 6`: Forecast horizons (+15, +30, +45, +60, +90, +120 minutes)
  - `C_out = 1`: Predicted convective reflectivity field
  - `H = 64, W = 64`: Future spatial grids corresponding to each forecast horizon

---

## 4. Layer Architecture & Structural Summary

```text
Input Sequence [B, 5, 1, 64, 64]
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ 1. Spatial Feature Encoder (Conv2D + BatchNorm + LReLU)│
│    Conv2D(1 -> 32, k=3, p=1) -> BatchNorm -> LeakyReLU │
│    Conv2D(32 -> 32, k=3, p=1) -> BatchNorm -> LeakyReLU│
└────────────────────────────────────────────────────────┘
      │ Encoded Sequence [B, 5, 32, 64, 64]
      ▼
┌────────────────────────────────────────────────────────┐
│ 2. Encoder ConvLSTM Core (2-Layer Recurrent Stack)     │
│    Layer 1: ConvLSTMCell(in=32, hid=32, k=3)           │
│    Layer 2: ConvLSTMCell(in=32, hid=64, k=3)           │
└────────────────────────────────────────────────────────┘
      │ Latent Final States (H_T, C_T) [B, 64, 64, 64]
      ▼
┌────────────────────────────────────────────────────────┐
│ 3. Forecaster Recurrent Core (Decoder ConvLSTM Cell)   │
│    ConvLSTMCell(in=64, hid=64, k=3)                    │
│    Rolls forward autoregressively for T_out steps      │
└────────────────────────────────────────────────────────┘
      │ Step Hidden States [B, 64, 64, 64]
      ▼
┌────────────────────────────────────────────────────────┐
│ 4. Spatial Output Projection Decoder                   │
│    Conv2D(64 -> 32, k=3, p=1) -> BatchNorm -> LeakyReLU│
│    Conv2D(32 -> 1, k=1) -> Linear / Sigmoid Projection │
└────────────────────────────────────────────────────────┘
      │
      ▼
Output Forecast Sequence [B, 6, 1, 64, 64]
```

---

## 5. Parameter Breakdown

| Module | Component | Kernel / Config | Parameters | Trainable |
| :--- | :--- | :--- | :--- | :--- |
| **Encoder** | `Conv2d(1, 32)` + `BatchNorm2d` | $3 \times 3, p=1$ | 384 | Yes |
| **Encoder** | `Conv2d(32, 32)` + `BatchNorm2d` | $3 \times 3, p=1$ | 9,312 | Yes |
| **ConvLSTM** | `ConvLSTMCell Layer 0` | $3 \times 3, in=32, hid=32$ | 73,856 | Yes |
| **ConvLSTM** | `ConvLSTMCell Layer 1` | $3 \times 3, in=32, hid=64$ | 221,440 | Yes |
| **Forecaster** | `ConvLSTMCell Decoder` | $3 \times 3, in=64, hid=64$ | 295,168 | Yes |
| **Decoder** | `Conv2d(64, 32)` + `BatchNorm2d` | $3 \times 3, p=1$ | 18,528 | Yes |
| **Decoder** | `Conv2d(32, 1)` | $1 \times 1$ | 33 | Yes |
| **Total** | **Full Network** | — | **618,721** | **618,721** |

---

## 6. PyTorch String Representation (`print(model)`)

```text
SpatiotemporalForecastNet(
  (encoder): Sequential(
    (0): Conv2d(1, 32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
    (1): BatchNorm2d(32, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
    (2): LeakyReLU(negative_slope=0.1, inplace=True)
    (3): Conv2d(32, 32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
    (4): BatchNorm2d(32, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
    (5): LeakyReLU(negative_slope=0.1, inplace=True)
  )
  (convlstm): ConvLSTM(
    (cells): ModuleList(
      (0): ConvLSTMCell(
        (conv): Conv2d(64, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
      )
      (1): ConvLSTMCell(
        (conv): Conv2d(96, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
      )
    )
  )
  (forecaster_cell): ConvLSTMCell(
    (conv): Conv2d(128, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
  )
  (decoder): Sequential(
    (0): Conv2d(64, 32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
    (1): BatchNorm2d(32, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
    (2): LeakyReLU(negative_slope=0.1, inplace=True)
    (3): Conv2d(32, 1, kernel_size=(1, 1), stride=(1, 1))
  )
)
```

---

## 7. Baseline Preservation

The previous optical-flow and velocity advection heuristic is preserved and exported as:
- `OpticalFlowAdvectionBaseline` in [`ml/extrapolator.py`](file:///Users/anjelosherin/Downloads/paper/ml/extrapolator.py)

This allows side-by-side comparison between the heuristic advection baseline and the trainable PyTorch spatiotemporal neural network.
