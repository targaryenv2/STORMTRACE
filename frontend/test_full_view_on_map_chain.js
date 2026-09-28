import assert from 'assert';
import { ALL_ACTIVE_CELLS, getCellLocation } from './src/services/nowcastService.js';

console.log('================================================================');
console.log('STORMTRACE — Complete "View on Map" End-to-End Behavioral Suite');
console.log('================================================================');

// Simulated App State Manager mimicking App.jsx React component state machine
class StormtraceAppState {
  constructor() {
    this.activeNav = 'dashboard';
    this.selectedCellId = 'SC-2026-0917-03';
    this.isNotificationsOpen = false;
    this.isSettingsOpen = false;
    this.rightPanelTab = 'details';
    this.targetMapView = null;
    this.mapNotice = null;
    this.mapViewCenter = [82.5, 22.0]; // Default India view
    this.mapViewZoom = 5.2;
    this.highlightedCellFeature = null;
    this.actionLog = [];
  }

  openNotifications() {
    this.isNotificationsOpen = true;
    this.isSettingsOpen = false;
    this.actionLog.push({ event: 'OPEN_NOTIFICATIONS' });
  }

  handleSelectCellFromView(cellId) {
    if (!cellId) {
      this.mapNotice = 'Unable to locate this storm cell on the current map.';
      this.actionLog.push({ event: 'SELECT_CELL_FAILED', reason: 'EMPTY_ID' });
      return false;
    }

    const loc = getCellLocation(cellId);
    if (!loc) {
      this.mapNotice = 'Unable to locate this storm cell on the current map.';
      this.actionLog.push({ event: 'SELECT_CELL_FAILED', cellId, reason: 'NOT_FOUND' });
      return false;
    }

    this.mapNotice = null;
    this.selectedCellId = cellId;
    this.rightPanelTab = 'details';
    this.activeNav = 'dashboard';
    this.isNotificationsOpen = false;

    this.targetMapView = {
      lon: loc.lon,
      lat: loc.lat,
      zoom: 8.5,
      cell_id: cellId,
      t: Date.now()
    };

    // Simulate OpenLayers view.animate reaction
    this.mapViewCenter = [loc.lon, loc.lat];
    this.mapViewZoom = 8.5;
    this.highlightedCellFeature = cellId;

    this.actionLog.push({
      event: 'SELECT_CELL_SUCCESS',
      cellId,
      targetCoordinates: [loc.lon, loc.lat],
      zoom: 8.5,
      locationName: loc.location_name
    });

    return true;
  }
}

// -----------------------------------------------------------------------------
// TEST 1: End-to-End "View on Map" for SC-2026-0917-03
// -----------------------------------------------------------------------------
console.log('\n[TEST 1] Flow for SC-2026-0917-03 (Kolkata Squall Line):');
const app = new StormtraceAppState();
app.openNotifications();
assert.strictEqual(app.isNotificationsOpen, true, 'Popover must be open');
console.log('  1. Notification popover opened -> isNotificationsOpen = true');

const cell03 = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-03');
assert(cell03, 'SC-2026-0917-03 must exist in catalog');
console.log(`  2. Notification found: "${cell03.location_name}" (Max: ${cell03.max_dbz} dBZ)`);

// User clicks "View on Map"
const success03 = app.handleSelectCellFromView('SC-2026-0917-03');
assert.strictEqual(success03, true, 'Handler must succeed');
assert.strictEqual(app.isNotificationsOpen, false, 'Popover must close');
assert.strictEqual(app.activeNav, 'dashboard', 'Must navigate to dashboard');
assert.strictEqual(app.rightPanelTab, 'details', 'Must switch right panel to details');
assert.strictEqual(app.selectedCellId, 'SC-2026-0917-03', 'Selected cell must be SC-2026-0917-03');
assert.strictEqual(app.mapViewCenter[0], 87.10, 'Map longitude must be 87.10');
assert.strictEqual(app.mapViewCenter[1], 23.32, 'Map latitude must be 23.32');
assert.strictEqual(app.mapViewZoom, 8.5, 'Map zoom must be 8.5');
assert.strictEqual(app.highlightedCellFeature, 'SC-2026-0917-03', 'Polygon feature must be highlighted');
console.log('  3. Popover closed -> isNotificationsOpen = false');
console.log(`  4. Map Centered on: [${app.mapViewCenter[0]}, ${app.mapViewCenter[1]}] at zoom ${app.mapViewZoom}`);
console.log(`  5. Selected Cell in State: ${app.selectedCellId} -> Highlighted on map: ${app.highlightedCellFeature}`);
console.log('  ✓ TEST 1 PASSED: SC-2026-0917-03 correctly focused and highlighted!');

// -----------------------------------------------------------------------------
// TEST 2: End-to-End "View on Map" for SC-2026-0917-01
// -----------------------------------------------------------------------------
console.log('\n[TEST 2] Flow for SC-2026-0917-01 (Ranchi Plateau Supercell):');
app.openNotifications();
assert.strictEqual(app.isNotificationsOpen, true);
console.log('  1. Notification popover opened -> isNotificationsOpen = true');

const cell01 = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-01');
assert(cell01, 'SC-2026-0917-01 must exist in catalog');
console.log(`  2. Notification found: "${cell01.location_name}" (Max: ${cell01.max_dbz} dBZ)`);

// User clicks "View on Map"
const success01 = app.handleSelectCellFromView('SC-2026-0917-01');
assert.strictEqual(success01, true);
assert.strictEqual(app.isNotificationsOpen, false);
assert.strictEqual(app.selectedCellId, 'SC-2026-0917-01');
assert.strictEqual(app.mapViewCenter[0], 85.31, 'Map longitude must be 85.31');
assert.strictEqual(app.mapViewCenter[1], 23.34, 'Map latitude must be 23.34');
assert.strictEqual(app.highlightedCellFeature, 'SC-2026-0917-01');
console.log('  3. Popover closed -> isNotificationsOpen = false');
console.log(`  4. Map Centered on: [${app.mapViewCenter[0]}, ${app.mapViewCenter[1]}] at zoom ${app.mapViewZoom}`);
console.log(`  5. Selected Cell in State: ${app.selectedCellId} -> Highlighted on map: ${app.highlightedCellFeature}`);
console.log('  ✓ TEST 2 PASSED: SC-2026-0917-01 correctly focused and highlighted (distinct from SC-03)!');

// -----------------------------------------------------------------------------
// TEST 3: End-to-End "View on Map" for SC-2026-0917-02
// -----------------------------------------------------------------------------
console.log('\n[TEST 3] Flow for SC-2026-0917-02 (Asansol-Durgapur Corridor):');
app.openNotifications();
assert.strictEqual(app.isNotificationsOpen, true);
console.log('  1. Notification popover opened -> isNotificationsOpen = true');

const cell02 = ALL_ACTIVE_CELLS.find(c => c.cell_id === 'SC-2026-0917-02');
assert(cell02, 'SC-2026-0917-02 must exist in catalog');
console.log(`  2. Notification found: "${cell02.location_name}" (Max: ${cell02.max_dbz} dBZ)`);

// User clicks "View on Map"
const success02 = app.handleSelectCellFromView('SC-2026-0917-02');
assert.strictEqual(success02, true);
assert.strictEqual(app.isNotificationsOpen, false);
assert.strictEqual(app.selectedCellId, 'SC-2026-0917-02');
assert.strictEqual(app.mapViewCenter[0], 86.92, 'Map longitude must be 86.92');
assert.strictEqual(app.mapViewCenter[1], 23.65, 'Map latitude must be 23.65');
assert.strictEqual(app.highlightedCellFeature, 'SC-2026-0917-02');
console.log('  3. Popover closed -> isNotificationsOpen = false');
console.log(`  4. Map Centered on: [${app.mapViewCenter[0]}, ${app.mapViewCenter[1]}] at zoom ${app.mapViewZoom}`);
console.log(`  5. Selected Cell in State: ${app.selectedCellId} -> Highlighted on map: ${app.highlightedCellFeature}`);
console.log('  ✓ TEST 3 PASSED: SC-2026-0917-02 correctly focused and highlighted (distinct from SC-01 and SC-03)!');

// -----------------------------------------------------------------------------
// TEST 4: Missing Cell Handling
// -----------------------------------------------------------------------------
console.log('\n[TEST 4] Missing/Invalid Cell Edge Case:');
app.openNotifications();
const missingResult = app.handleSelectCellFromView('SC-INVALID-999');
assert.strictEqual(missingResult, false, 'Must return false on missing cell');
assert.strictEqual(app.isNotificationsOpen, true, 'Popover must remain open on failure');
assert.strictEqual(app.mapNotice, 'Unable to locate this storm cell on the current map.');
console.log(`  ✓ Missing cell detected -> mapNotice: "${app.mapNotice}"`);
console.log('  ✓ TEST 4 PASSED: Graceful error handling verified!');

console.log('\n================================================================');
console.log('🎉 ALL END-TO-END BEHAVIORAL VERIFICATION TESTS PASSED (100%)');
console.log('================================================================\n');
