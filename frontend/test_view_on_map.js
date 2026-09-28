import { ALL_ACTIVE_CELLS, getCellLocation } from './src/services/nowcastService.js';
import assert from 'assert';

console.log('====================================================');
console.log('STORMTRACE — "View on Map" Automated Verification');
console.log('====================================================');

// Test 1: Severe storm notifications contain valid cell IDs
console.log('\n[TEST 1] Verifying severe storm notification cell IDs...');
const severeCells = ALL_ACTIVE_CELLS.filter(c => c.warning_level === 'RED' || c.warning_level === 'ORANGE');
assert(severeCells.length >= 3, 'Expected at least 3 severe cells');

const requiredCellIds = ['SC-2026-0917-03', 'SC-2026-0917-01', 'SC-2026-0917-02'];
for (const id of requiredCellIds) {
  const found = severeCells.find(c => c.cell_id === id);
  assert(found, `Required cell ${id} not found in severe cells`);
  console.log(`  ✓ Cell ${id} (${found.warning_level}) — Found: ${found.location_name}`);
}

// Test 2: getCellLocation resolves exact centroid coordinates
console.log('\n[TEST 2] Testing getCellLocation resolution...');
for (const id of requiredCellIds) {
  const loc = getCellLocation(id);
  assert(loc !== null, `getCellLocation failed for ${id}`);
  assert(typeof loc.lon === 'number' && !isNaN(loc.lon), `Invalid longitude for ${id}`);
  assert(typeof loc.lat === 'number' && !isNaN(loc.lat), `Invalid latitude for ${id}`);
  assert(loc.zoom >= 8.0, `Expected zoom >= 8.0 for storm level, got ${loc.zoom}`);
  console.log(`  ✓ ${id} -> lon: ${loc.lon}, lat: ${loc.lat}, zoom: ${loc.zoom}, severity: ${loc.severity_score}`);
}

// Test 3: Verify multiple notifications focus DIFFERENT cells (no hardcoded coordinates)
console.log('\n[TEST 3] Verifying distinct coordinates for different cells...');
const loc3 = getCellLocation('SC-2026-0917-03');
const loc1 = getCellLocation('SC-2026-0917-01');
const loc2 = getCellLocation('SC-2026-0917-02');

assert(loc3.lon !== loc1.lon || loc3.lat !== loc1.lat, 'SC-03 and SC-01 coordinates must differ');
assert(loc3.lon !== loc2.lon || loc3.lat !== loc2.lat, 'SC-03 and SC-02 coordinates must differ');
assert(loc1.lon !== loc2.lon || loc1.lat !== loc2.lat, 'SC-01 and SC-02 coordinates must differ');
console.log('  ✓ SC-2026-0917-03 (Kolkata/East India):', loc3.lon, loc3.lat);
console.log('  ✓ SC-2026-0917-01 (Ranchi Plateau):    ', loc1.lon, loc1.lat);
console.log('  ✓ SC-2026-0917-02 (Asansol-Durgapur):  ', loc2.lon, loc2.lat);

// Test 4: Missing cell handling
console.log('\n[TEST 4] Testing missing/invalid storm cell handling...');
assert.strictEqual(getCellLocation('SC-UNKNOWN-999'), null, 'Expected null for unknown cell ID');
assert.strictEqual(getCellLocation(''), null, 'Expected null for empty cell ID');
assert.strictEqual(getCellLocation(null), null, 'Expected null for null cell ID');
console.log('  ✓ Missing cells return null cleanly without errors');

// Test 5: Check all active cells in dataset
console.log('\n[TEST 5] Checking complete ALL_ACTIVE_CELLS catalog...');
for (const cell of ALL_ACTIVE_CELLS) {
  const loc = getCellLocation(cell.cell_id);
  assert(loc !== null, `Catalog cell ${cell.cell_id} must resolve location`);
  assert(loc.cell_id === cell.cell_id);
  console.log(`  ✓ [${cell.cell_id}] ${cell.location_name} -> [${loc.lon.toFixed(2)}, ${loc.lat.toFixed(2)}]`);
}

console.log('\n====================================================');
console.log('🎉 ALL 5 TEST SUITES PASSED SUCCESSFULLY!');
console.log('====================================================\n');
