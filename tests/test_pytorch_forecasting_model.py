#!/usr/bin/env python3
"""
STORMTRACE PyTorch Spatiotemporal Forecasting Model Test Suite
================================================================================
Comprehensive verification tests for the genuine PyTorch Spatiotemporal ConvLSTM
forecasting neural network architecture.
================================================================================
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
import torch.nn as nn
import torch.optim as optim

from ml.models.spatiotemporal_model import (
    ModelConfig,
    ConvLSTMCell,
    ConvLSTM,
    SpatiotemporalForecastNet,
    StormTraceConvLSTMNet
)


class TestPyTorchForecastingModel(unittest.TestCase):
    """Test suite verifying the genuine PyTorch Spatiotemporal ConvLSTM architecture."""

    def setUp(self):
        torch.manual_seed(42)
        self.default_config = ModelConfig(
            in_channels=1,
            out_channels=1,
            hidden_dims=[16, 32],
            kernel_size=3,
            num_layers=2,
            in_seq_len=5,
            out_seq_len=6,
            spatial_height=32,
            spatial_width=32
        )

    def test_01_imports_and_alias(self):
        """Test 1: Verify model imports, class inheritance, and aliases."""
        from ml.model import StormTraceConvLSTMNet as ModelAlias
        self.assertIs(StormTraceConvLSTMNet, SpatiotemporalForecastNet)
        self.assertIs(ModelAlias, SpatiotemporalForecastNet)
        self.assertTrue(issubclass(SpatiotemporalForecastNet, nn.Module))
        self.assertTrue(issubclass(ConvLSTMCell, nn.Module))
        self.assertTrue(issubclass(ConvLSTM, nn.Module))

    def test_02_convlstm_cell_gates(self):
        """Test 2: Verify ConvLSTM cell computes all 4 gates and updates state."""
        cell = ConvLSTMCell(in_channels=4, hidden_dim=8, kernel_size=3)
        b, h, w = 2, 16, 16
        x = torch.randn(b, 4, h, w)
        h_prev = torch.randn(b, 8, h, w)
        c_prev = torch.randn(b, 8, h, w)

        h_next, c_next = cell(x, (h_prev, c_prev))
        self.assertEqual(h_next.shape, (b, 8, h, w))
        self.assertEqual(c_next.shape, (b, 8, h, w))
        self.assertTrue(torch.isfinite(h_next).all())
        self.assertTrue(torch.isfinite(c_next).all())

        # Test initialization without prior hidden state
        h_init, c_init = cell(x, None)
        self.assertEqual(h_init.shape, (b, 8, h, w))
        self.assertEqual(c_init.shape, (b, 8, h, w))

    def test_03_trainable_parameters_count(self):
        """Test 3: Verify model contains positive count of trainable parameters."""
        model = SpatiotemporalForecastNet(self.default_config)
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        self.assertGreater(total_params, 0)
        self.assertGreater(trainable_params, 0)
        self.assertEqual(model.total_parameters, total_params)
        self.assertEqual(model.trainable_parameters, trainable_params)
        self.assertEqual(model.non_trainable_parameters, 0)
        print(f"\n[Test] Model Total Parameters: {total_params:,} | Trainable: {trainable_params:,}")

    def test_04_forward_pass_and_output_contract(self):
        """Test 4: Verify 5D input tensor is accepted and produces correct 5D output contract."""
        model = SpatiotemporalForecastNet(self.default_config)
        batch_size = 2
        in_t = self.default_config.in_seq_len
        out_t = self.default_config.out_seq_len
        c_in = self.default_config.in_channels
        c_out = self.default_config.out_channels
        h = self.default_config.spatial_height
        w = self.default_config.spatial_width

        input_tensor = torch.randn(batch_size, in_t, c_in, h, w)
        output_tensor = model(input_tensor)

        expected_shape = (batch_size, out_t, c_out, h, w)
        self.assertEqual(output_tensor.shape, expected_shape)
        self.assertTrue(torch.isfinite(output_tensor).all())

    def test_05_variable_future_steps(self):
        """Test 5: Verify model can produce variable future forecast horizons."""
        model = SpatiotemporalForecastNet(self.default_config)
        input_tensor = torch.randn(1, 4, 1, 32, 32)

        for future_steps in [1, 3, 6, 8]:
            out = model(input_tensor, future_steps=future_steps)
            self.assertEqual(out.shape, (1, future_steps, 1, 32, 32))

    def test_06_loss_and_backpropagation(self):
        """Test 6: Verify loss computation and backpropagation populate gradients."""
        model = SpatiotemporalForecastNet(self.default_config)
        input_tensor = torch.randn(2, 5, 1, 32, 32)
        target_tensor = torch.randn(2, 6, 1, 32, 32)

        output = model(input_tensor)
        loss = nn.MSELoss()(output, target_tensor)

        self.assertTrue(torch.isfinite(loss))
        self.assertGreater(loss.item(), 0.0)

        # Ensure gradients are currently None
        for p in model.parameters():
            self.assertIsNone(p.grad)

        # Backward pass
        loss.backward()

        # Check gradients are populated and non-zero
        has_grad = False
        for name, p in model.named_parameters():
            if p.requires_grad:
                self.assertIsNotNone(p.grad, f"Parameter {name} has None grad after backward()")
                self.assertTrue(torch.isfinite(p.grad).all(), f"Parameter {name} has non-finite grad")
                if p.grad.abs().sum() > 0:
                    has_grad = True

        self.assertTrue(has_grad, "No non-zero gradients were produced during backprop")

    def test_07_optimizer_updates_weights(self):
        """Test 7: Verify optimizer.step() changes model parameters (genuine gradient descent)."""
        model = SpatiotemporalForecastNet(self.default_config)
        optimizer = optim.Adam(model.parameters(), lr=1e-3)

        # Save initial weights snapshot
        initial_params = [p.clone().detach() for p in model.parameters()]

        input_tensor = torch.randn(2, 5, 1, 32, 32)
        target_tensor = torch.randn(2, 6, 1, 32, 32)

        # Optimization step
        optimizer.zero_grad()
        output = model(input_tensor)
        loss = nn.MSELoss()(output, target_tensor)
        loss.backward()
        optimizer.step()

        # Verify weights have changed
        changed_count = 0
        for p_init, p_now in zip(initial_params, model.parameters()):
            diff = (p_init - p_now).abs().sum().item()
            if diff > 1e-7:
                changed_count += 1

        self.assertGreater(changed_count, 0, "Optimizer step did not modify any model weights")
        print(f"[Test] {changed_count} parameter tensors updated by optimizer.step()")

    def test_08_temporal_sequence_sensitivity(self):
        """Test 8: Verify that changing past temporal sequence frames alters forecast output."""
        model = SpatiotemporalForecastNet(self.default_config)
        model.eval()

        input_seq_1 = torch.randn(1, 5, 1, 32, 32)
        input_seq_2 = input_seq_1.clone()
        # Perturb only the earliest historical frame (T-60)
        input_seq_2[:, 0, :, :, :] += 2.5

        with torch.no_grad():
            out_1 = model(input_seq_1)
            out_2 = model(input_seq_2)

        diff = (out_1 - out_2).abs().sum().item()
        self.assertGreater(diff, 1e-4, "Model output is invariant to changes in historical time sequence")

    def test_09_multimodal_channel_support(self):
        """Test 9: Verify support for multi-channel input modalities (e.g. Radar + Satellite + NWP)."""
        multi_config = ModelConfig(
            in_channels=5,  # 5 modalities: radar, sat_ir, cape, imerg, wglc
            out_channels=2, # 2 outputs: reflectivity dBZ, thunderstorm prob
            hidden_dims=[16, 32],
            spatial_height=32,
            spatial_width=32
        )
        model = SpatiotemporalForecastNet(multi_config)
        input_tensor = torch.randn(2, 5, 5, 32, 32)
        output = model(input_tensor)
        self.assertEqual(output.shape, (2, 6, 2, 32, 32))

    def test_10_checkpoint_save_and_reload(self):
        """Test 10: Verify state_dict checkpoint saving and exact weight restoration."""
        model = SpatiotemporalForecastNet(self.default_config)
        optimizer = optim.Adam(model.parameters(), lr=1e-3)

        input_tensor = torch.randn(1, 5, 1, 32, 32)
        with torch.no_grad():
            expected_output = model(input_tensor)

        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = os.path.join(tmpdir, "test_checkpoint.pt")
            model.save_checkpoint(
                ckpt_path,
                optimizer=optimizer,
                epoch=1,
                extra_metadata={"test_run": True}
            )
            self.assertTrue(os.path.exists(ckpt_path))

            # Reload model from checkpoint
            loaded_model, ckpt_meta = SpatiotemporalForecastNet.load_checkpoint(ckpt_path)
            self.assertEqual(ckpt_meta["model_architecture"], "StormTrace_ConvLSTM_ForecastNet")
            self.assertEqual(ckpt_meta["epoch"], 1)

            with torch.no_grad():
                loaded_output = loaded_model(input_tensor)

            # Check exact tensor match
            diff = (expected_output - loaded_output).abs().max().item()
            self.assertAlmostEqual(diff, 0.0, places=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
