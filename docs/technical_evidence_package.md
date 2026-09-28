# STORMTRACE Technical Evidence & Scientific Architecture Package

**Version**: 2.0-Verified  
**Target Domain**: Regional East India ($83.5^\circ\text{E} - 89.8^\circ\text{E}, 20.0^\circ\text{N} - 26.3^\circ\text{N}$)  
**Verification State**: **STATE B (IMPLEMENTED & LOCALLY VERIFIED)**  
**Production Training State**: **DEFERRED PENDING VERIFIED 2020+ EAST INDIA DATASETS**

---

## 1. System Implementation & Provenance Overview

| Component | Verified Implementation Status | Evidence / File | Scientific Notes |
| :--- | :--- | :--- | :--- |
| **Spatiotemporal Neural Network** | **STATE B (VERIFIED)** | `ml/models/spatiotemporal_model.py` | Genuine PyTorch `ConvLSTM` architecture with 618,721 trainable parameters. |
| **Neural Multimodal Fusion** | **STATE B (VERIFIED)** | `ml/models/multimodal_convlstm.py` | 5-modality dynamic gated fusion with missing-sensor mask tensors. |
| **Kinematic Advection Baseline** | **STATE B (VERIFIED)** | `ml/extrapolator.py` | Preserved as `OpticalFlowAdvectionBaseline` for scientific comparison. |
| **Temporal Sequence Builder** | **STATE B (VERIFIED)** | `ml/datasets/temporal_radar_dataset.py` | Enforces 5-frame input ($T-60\dots T0$) and 6-frame target ($T+15\dots T+120$). |
| **Leakage Auditor** | **STATE B (VERIFIED)** | `ml/datasets/leakage_checker.py` | Automated chronological split auditor preventing future-frame leakage. |
| **Future-Frame Evaluator** | **STATE B (VERIFIED)** | `ml/evaluation/future_frame_evaluator.py` | Multi-horizon verification vs actual future observations at $T0 + \Delta t$. |
| **Meteorological Metrics Engine** | **STATE B (VERIFIED)** | `ml/evaluation/metrics.py` | Dynamic CSI, POD, FAR, HSS, Brier score, and RMSE calculation. |
| **Neural MC-Dropout Uncertainty** | **STATE B (VERIFIED)** | `ml/models/spatiotemporal_model.py` | 25 stochastic forward passes evaluating predictive variance. |
| **Motion Vector Estimator** | **STATE B (VERIFIED)** | `ml/tracking/motion_estimator.py` | Calculates $(\Delta x / \Delta t, \Delta y / \Delta t)$, speed in km/h, and compass heading. |
| **Probability Calibration** | **STATE B (VERIFIED)** | `ml/calibration/prob_calibrator.py` | Platt scaling & isotonic regression engine with reliability diagram bins. |
| **Real Radar Ingestion Pipeline** | **STATE B (VERIFIED)** | `dataset/loaders/radar_loader.py` | Validated using 69 NetCDF files from 2018 ISRO TERLS DWR (South India). |
| **AI Assistant Grounding** | **STATE B (VERIFIED)** | `backend/stormtrace/ai/` | Google Gemini `gemini-2.5-flash` with strict factual grounding rules. |
| **Final East India Production Model** | **STATE C (DEFERRED)** | `ml/train_conv_lstm.py` | Awaiting verified 2020+ East India IMD DWR and MOSDAC NetCDF data. |

---

## 2. Spatiotemporal ConvLSTM Mathematical Formulation

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

## 3. Loss Function Formulation (Weighted Convective Loss)

To counteract regression-to-the-mean and prevent the network from blurring high-intensity convective cores, the loss function applies a non-linear weighting mask $w(y)$:

$$w(y_{b,t,c,i,j}) = \begin{cases} 4.0 & \text{if } y_{b,t,c,i,j} \ge 0.50 \text{ (i.e. } \ge 35.0\text{ dBZ)} \\ 1.0 & \text{otherwise} \end{cases}$$

$$\mathcal{L}_{\text{W-MSE}} = \frac{1}{B \cdot T_{\text{out}} \cdot C \cdot H \cdot W} \sum_{b,t,c,i,j} w(y_{b,t,c,i,j}) \cdot \left( y_{b,t,c,i,j} - \hat{y}_{b,t,c,i,j} \right)^2$$

---

## 4. Multi-Horizon Forecast Contract

- **Historical Input**: `[B, 5, 1, 64, 64]` ($T-60, T-45, T-30, T-15, T0$)
- **Future Horizons**: `[B, 6, 1, 64, 64]`
  - Horizon 1: **+15 min** (Tactical severe downburst hazard)
  - Horizon 2: **+30 min** (Airport terminal area & runway operations)
  - Horizon 3: **+45 min** (Airspace rerouting & squall line warning)
  - Horizon 4: **+60 min** (District municipal alert & flood readiness)
  - Horizon 5: **+90 min** (Convective cell cluster evolution)
  - Horizon 6: **+120 min** (Mesoscale system propagation & dissipation)

---

## 5. Verification Metrics Definition

- **Critical Success Index (CSI)**:
  $$\text{CSI} = \frac{\text{Hits}}{\text{Hits} + \text{Misses} + \text{False Alarms}}$$
- **Probability of Detection (POD)**:
  $$\text{POD} = \frac{\text{Hits}}{\text{Hits} + \text{Misses}}$$
- **False Alarm Ratio (FAR)**:
  $$\text{FAR} = \frac{\text{False Alarms}}{\text{Hits} + \text{False Alarms}}$$
- **Brier Score (BS)**:
  $$\text{BS} = \frac{1}{N} \sum_{k=1}^N (p_k - o_k)^2$$

---

## 6. Scientific Data Governance & Ethical Integrity Rules

1. **Zero Fabrication**: No synthetic predictions or uncalibrated outputs are disguised as verified live radar observations.
2. **TERLS Radar Isolation**: The 2018 ISRO TERLS DWR dataset (Thumba, Kerala) is strictly documented as a South India radar pipeline validation fixture; it is never claimed as East India training data.
3. **Climatological Baseline Distinction**: WGLC lightning is strictly exposed as a 2010–2020 monthly climatology mean, never as an active real-time lightning sensor.
4. **Advisory Disclaimer**: All user-facing interfaces and API endpoints display the mandatory operational advisory: *"This is AI decision-support, not an official IMD warning."*
