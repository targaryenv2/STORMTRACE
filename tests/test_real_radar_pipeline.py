#!/usr/bin/env python3
"""
STORMTRACE Real Radar Data Pipeline Test Suite
Validates real ISRO TERLS Doppler Weather Radar (DWR) NetCDF ingestion,
volumetric DBZ/VEL extraction, temporal inventory, domain compatibility,
and multi-frame tensor preprocessing.
"""

import unittest
import os
import sys
import glob

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataset.loaders.radar_loader import RadarDataLoader
from dataset.grid import StormTraceGrid
from dataset.provenance import DataType


class TestRealRadarPipeline(unittest.TestCase):
    """Automated verification of the real TERLS DWR NetCDF ingestion pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.loader = RadarDataLoader('data/raw/radar/terls')
        cls.files = cls.loader.discover_real_files()

    def test_01_real_files_discovery(self):
        """Check that all 69 NetCDF files are discovered and sorted."""
        self.assertEqual(len(self.files), 69, f'Expected 69 files, found {len(self.files)}')
        self.assertTrue(self.files[0]['filepath'].endswith('.nc'))
        self.assertEqual(self.files[0]['source_instrument'], 'ISRO TERLS DWR')
        self.assertEqual(self.files[0]['format'], 'NetCDF')

    def test_02_timestamp_extraction(self):
        """Check filename and NetCDF timestamp parsing."""
        first_file = self.files[0]
        self.assertEqual(first_file['timestamp_utc'], '2018-01-11T00:12:14Z')
        last_file = self.files[-1]
        self.assertEqual(last_file['timestamp_utc'], '2018-01-11T23:55:14Z')

    def test_03_netcdf_header_and_dimensions(self):
        """Check NetCDF dimensions (height=81, lat=481, lon=481, time=0)."""
        header = self.loader.read_netcdf_header(self.files[0]['filepath'])
        dims = header['dims']
        self.assertEqual(dims['height'], 81)
        self.assertEqual(dims['lat'], 481)
        self.assertEqual(dims['lon'], 481)
        self.assertIn('DBZ', header['variables'])
        self.assertIn('VEL', header['variables'])
        self.assertIn('latitude', header['variables'])
        self.assertIn('longitude', header['variables'])

    def test_04_coordinate_extraction(self):
        """Check extracted geographic and vertical coordinates."""
        frame = self.loader.read_terls_netcdf_frame(self.files[0]['filepath'], extract_vel=True)
        spatial = frame['spatial_extent']
        self.assertAlmostEqual(spatial['lat_min'], 6.3708, places=3)
        self.assertAlmostEqual(spatial['lat_max'], 10.7125, places=3)
        self.assertAlmostEqual(spatial['lon_min'], 74.6867, places=3)
        self.assertAlmostEqual(spatial['lon_max'], 79.0236, places=3)
        self.assertEqual(len(frame['heights']), 81)

    def test_05_dbz_reflectivity_extraction(self):
        """Check 2D composite DBZ computation and physical range validation."""
        frame = self.loader.read_terls_netcdf_frame(self.files[0]['filepath'], extract_vel=False)
        dbz = frame['reflectivity_dbz']
        self.assertEqual(len(dbz), 481)
        self.assertEqual(len(dbz[0]), 481)
        self.assertGreater(frame['max_dbz'], 45.0, 'Convective core max dBZ should exceed 45 dBZ')
        self.assertLessEqual(frame['max_dbz'], 75.0, 'Reflectivity must remain physically bounded <= 75 dBZ')
        self.assertGreater(frame['convective_core_count'], 100, 'Should detect active convective core pixels')

    def test_06_vel_radial_velocity_extraction(self):
        """Check Doppler radial velocity (VEL) extraction and physical limits."""
        frame = self.loader.read_terls_netcdf_frame(self.files[0]['filepath'], extract_vel=True)
        vel = frame['velocity_radial_mps']
        self.assertIsNotNone(vel)
        self.assertEqual(len(vel), 481)
        self.assertEqual(len(vel[0]), 481)

    def test_07_missing_value_handling(self):
        """Verify that missing radar background (NaNs) are converted to 0.0 with reported statistics."""
        frame = self.loader.read_terls_netcdf_frame(self.files[0]['filepath'])
        self.assertGreater(frame['missing_value_pct'], 80.0, 'Background radar range should have high missing %')
        # Ensure no NaNs in output matrix
        for row in frame['reflectivity_dbz']:
            for val in row:
                self.assertFalse(val != val, 'NaN found in processed reflectivity grid')

    def test_08_provenance_registration(self):
        """Verify strict provenance classification: REAL_OBSERVATION, ISRO TERLS DWR, non-synthetic."""
        frame = self.loader.read_terls_netcdf_frame(self.files[0]['filepath'])
        prov = frame['provenance']
        self.assertEqual(prov['data_type'], DataType.REAL_OBSERVATION.value)
        self.assertEqual(prov['source'], 'ISRO TERLS DWR')
        self.assertIn('2018-01-11', prov['observation_period'])
        self.assertFalse(frame['is_demo'])
        self.assertTrue(frame['is_real_observation'])
        self.assertNotIn('SYNTHETIC', prov['data_type'])

    def test_09_geographic_domain_compatibility(self):
        """Verify that TERLS South India radar is flagged as OUTSIDE East India domain."""
        frame = self.loader.read_terls_netcdf_frame(self.files[0]['filepath'])
        grid_east_india = StormTraceGrid.regional_east_india()
        compat = self.loader.evaluate_grid_compatibility(frame['spatial_extent'], grid_east_india)
        self.assertFalse(compat['compatible'])
        self.assertEqual(compat['status'], 'REAL RADAR DATA — OUTSIDE CURRENT STORMTRACE TRAINING DOMAIN')
        self.assertIn('completely disjoint', compat['message'])

    def test_10_temporal_inventory(self):
        """Verify temporal inventory statistics across all 69 files."""
        inv = self.loader.create_temporal_inventory(self.files)
        self.assertEqual(inv['total_files_discovered'], 69)
        self.assertEqual(inv['successfully_opened'], 69)
        self.assertEqual(inv['corrupted_files_count'], 0)
        self.assertEqual(len(inv['duplicate_timestamps']), 0)
        self.assertTrue(inv['all_files_have_dbz'])
        self.assertTrue(inv['all_files_have_vel'])
        self.assertAlmostEqual(inv['mean_interval_minutes'], 20.93, delta=0.5)

    def test_11_sequence_preprocessing(self):
        """Verify 5-frame sequence preprocessing into normalized input tensor."""
        seq = self.loader.preprocess_sequence(
            [f['filepath'] for f in self.files[:5]],
            target_grid=StormTraceGrid.regional_east_india(),
            normalize=True
        )
        self.assertEqual(seq['status'], 'PREPROCESSED_SUCCESS')
        self.assertEqual(seq['frame_count'], 5)
        self.assertEqual(seq['tensor_shape'], [5, 64, 64, 1])
        self.assertTrue(seq['normalized'])
        self.assertEqual(len(seq['observed_max_dbz_per_frame']), 5)
        self.assertFalse(seq['domain_compatibility']['compatible'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
