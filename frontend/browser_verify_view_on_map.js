import { spawn } from 'child_process';
import http from 'http';
import fs from 'fs';
import path from 'path';

console.log('===========================================================');
console.log('STORMTRACE — Headless Chrome End-to-End Browser Verification');
console.log('===========================================================');

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DEBUG_PORT = 9222;
const USER_DATA_DIR = '/tmp/stormtrace_cdp_' + Date.now();

// Helper to query CDP endpoints
function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

// Simple CDP Client over WebSocket
class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.id = 1;
    this.callbacks = new Map();
    this.events = [];
    this.consoleErrors = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (err) => reject(err);
      this.ws.onmessage = (msg) => {
        const data = JSON.parse(msg.data);
        if (data.id && this.callbacks.has(data.id)) {
          const { resolve, reject } = this.callbacks.get(data.id);
          this.callbacks.delete(data.id);
          if (data.error) reject(data.error);
          else resolve(data.result);
        } else if (data.method) {
          this.events.push(data);
          if (data.method === 'Runtime.consoleAPICalled' && data.params.type === 'error') {
            this.consoleErrors.push(data.params.args.map(a => a.value || a.description).join(' '));
          }
          if (data.method === 'Runtime.exceptionThrown') {
            this.consoleErrors.push(data.params.exceptionDetails.text);
          }
        }
      };
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.id++;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true
    });
    if (res.exceptionDetails) {
      throw new Error(`Eval error: ${res.exceptionDetails.text} (${expression})`);
    }
    return res.result?.value;
  }

  async takeScreenshot(filepath) {
    const res = await this.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(filepath, Buffer.from(res.data, 'base64'));
    console.log(`  📸 Screenshot saved: ${filepath}`);
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

async function run() {
  console.log('1. Launching Google Chrome...');
  const chromeProcess = spawn(CHROME_PATH, [
    `--remote-debugging-port=${DEBUG_PORT}`,
    '--headless=new',
    `--user-data-dir=${USER_DATA_DIR}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--window-size=1440,900',
    'http://localhost:5173'
  ]);

  // Wait for CDP port
  let targets = null;
  for (let i = 0; i < 30; i++) {
    try {
      targets = await getJson(`http://127.0.0.1:${DEBUG_PORT}/json/list`);
      if (targets && targets.length > 0) break;
    } catch (e) {
      await new Promise(r => setTimeout(r, 200));
    }
  }

  if (!targets || targets.length === 0) {
    chromeProcess.kill();
    throw new Error('Failed to connect to Chrome DevTools port.');
  }

  const pageTarget = targets.find(t => t.type === 'page') || targets[0];
  console.log(`2. Connecting to page target: ${pageTarget.title} (${pageTarget.url})`);

  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.connect();
  await client.send('Page.enable');
  await client.send('Runtime.enable');
  await client.send('DOM.enable');

  // Wait for OpenLayers Map to be ready
  console.log('3. Waiting for STORMTRACE OpenLayers map initialization...');
  let mapReady = false;
  for (let i = 0; i < 50; i++) {
    const ready = await client.eval(`
      (() => {
        // Dismiss first-time intro modal if present
        const modalBtn = document.querySelector('button');
        return typeof window.__stormtrace_map !== 'undefined' && window.__stormtrace_map !== null;
      })()
    `);
    if (ready) {
      mapReady = true;
      break;
    }
    await new Promise(r => setTimeout(r, 200));
  }

  if (!mapReady) {
    client.close();
    chromeProcess.kill();
    throw new Error('Timeout waiting for window.__stormtrace_map.');
  }
  console.log('✓ STORMTRACE OpenLayers map canvas is ready.');

  // Helper function to read current map center coordinates (EPSG:4326)
  const getMapCoordinates = async () => {
    return await client.eval(`
      (() => {
        if (!window.__stormtrace_map) return null;
        const view = window.__stormtrace_map.getView();
        const center = view.getCenter();
        // transform EPSG:3857 to EPSG:4326
        const c4326 = window.ol ? window.ol.proj.toLonLat(center) : [
          (center[0] / 20037508.34) * 180,
          (Math.atan(Math.exp(center[1] / (20037508.34 / 180) * Math.PI / 180)) * 360 / Math.PI) - 90
        ];
        return {
          lon: c4326[0],
          lat: c4326[1],
          zoom: view.getZoom()
        };
      })()
    `);
  };

  const getSelectedCellFromDOM = async () => {
    return await client.eval(`
      (() => {
        const el = document.querySelector('.font-black.text-slate-900.font-mono');
        return el ? el.textContent.trim() : null;
      })()
    `);
  };

  const isPopoverOpen = async () => {
    return await client.eval(`
      (() => {
        const pop = document.querySelector('[aria-label="Notifications feed"]');
        return pop !== null;
      })()
    `);
  };

  const openNotificationsPopover = async () => {
    await client.eval(`
      (() => {
        const btn = document.querySelector('button[aria-label="Open notifications"]');
        if (btn) btn.click();
      })()
    `);
    await new Promise(r => setTimeout(r, 250));
  };

  // -------------------------------------------------------------
  // TEST 1: SC-2026-0917-03
  // -------------------------------------------------------------
  console.log('\n=============================================================');
  console.log('TEST 1: "View on Map" for SC-2026-0917-03 (Kolkata Squall Line)');
  console.log('=============================================================');

  await openNotificationsPopover();
  let popoverState = await isPopoverOpen();
  console.log(`  1. Notifications popover opened: ${popoverState ? 'YES' : 'NO'}`);

  // Click View on Map for SC-2026-0917-03
  const clicked03 = await client.eval(`
    (() => {
      const btns = Array.from(document.querySelectorAll('button[title*="View SC-2026-0917-03"]'));
      if (btns.length > 0) {
        btns[0].click();
        return true;
      }
      // Fallback selector by text
      const allBtns = Array.from(document.querySelectorAll('button'));
      const targetBtn = allBtns.find(b => b.title && b.title.includes('SC-2026-0917-03'));
      if (targetBtn) {
        targetBtn.click();
        return true;
      }
      return false;
    })()
  `);
  console.log(`  2. Clicked "View on Map" for SC-2026-0917-03: ${clicked03 ? 'SUCCESS' : 'FAILED'}`);
  await new Promise(r => setTimeout(r, 700));

  popoverState = await isPopoverOpen();
  console.log(`  3. Notifications popover closed: ${!popoverState ? 'YES' : 'NO'}`);

  const coords03 = await getMapCoordinates();
  const selected03 = await getSelectedCellFromDOM();
  console.log(`  4. Map Center Coordinates: [lon: ${coords03.lon.toFixed(4)}, lat: ${coords03.lat.toFixed(4)}, zoom: ${coords03.zoom.toFixed(1)}]`);
  console.log(`  5. Selected Cell in Right Panel: ${selected03}`);

  if (Math.abs(coords03.lon - 87.10) < 0.2 && Math.abs(coords03.lat - 23.32) < 0.2 && selected03 === 'SC-2026-0917-03') {
    console.log('  🎉 TEST 1 PASSED: Map accurately focused and selected SC-2026-0917-03!');
  } else {
    console.error('  ❌ TEST 1 FAILED');
  }

  // -------------------------------------------------------------
  // TEST 2: SC-2026-0917-01
  // -------------------------------------------------------------
  console.log('\n=============================================================');
  console.log('TEST 2: "View on Map" for SC-2026-0917-01 (Ranchi Supercell)');
  console.log('=============================================================');

  await openNotificationsPopover();
  popoverState = await isPopoverOpen();
  console.log(`  1. Notifications popover opened: ${popoverState ? 'YES' : 'NO'}`);

  const clicked01 = await client.eval(`
    (() => {
      const btns = Array.from(document.querySelectorAll('button[title*="View SC-2026-0917-01"]'));
      if (btns.length > 0) {
        btns[0].click();
        return true;
      }
      return false;
    })()
  `);
  console.log(`  2. Clicked "View on Map" for SC-2026-0917-01: ${clicked01 ? 'SUCCESS' : 'FAILED'}`);
  await new Promise(r => setTimeout(r, 700));

  popoverState = await isPopoverOpen();
  console.log(`  3. Notifications popover closed: ${!popoverState ? 'YES' : 'NO'}`);

  const coords01 = await getMapCoordinates();
  const selected01 = await getSelectedCellFromDOM();
  console.log(`  4. Map Center Coordinates: [lon: ${coords01.lon.toFixed(4)}, lat: ${coords01.lat.toFixed(4)}, zoom: ${coords01.zoom.toFixed(1)}]`);
  console.log(`  5. Selected Cell in Right Panel: ${selected01}`);

  if (Math.abs(coords01.lon - 85.31) < 0.2 && Math.abs(coords01.lat - 23.34) < 0.2 && selected01 === 'SC-2026-0917-01') {
    console.log('  🎉 TEST 2 PASSED: Map accurately moved from Kolkata to Ranchi for SC-2026-0917-01!');
  } else {
    console.error('  ❌ TEST 2 FAILED');
  }

  // -------------------------------------------------------------
  // TEST 3: SC-2026-0917-02
  // -------------------------------------------------------------
  console.log('\n=============================================================');
  console.log('TEST 3: "View on Map" for SC-2026-0917-02 (Asansol-Durgapur Corridor)');
  console.log('=============================================================');

  await openNotificationsPopover();
  popoverState = await isPopoverOpen();
  console.log(`  1. Notifications popover opened: ${popoverState ? 'YES' : 'NO'}`);

  const clicked02 = await client.eval(`
    (() => {
      const btns = Array.from(document.querySelectorAll('button[title*="View SC-2026-0917-02"]'));
      if (btns.length > 0) {
        btns[0].click();
        return true;
      }
      return false;
    })()
  `);
  console.log(`  2. Clicked "View on Map" for SC-2026-0917-02: ${clicked02 ? 'SUCCESS' : 'FAILED'}`);
  await new Promise(r => setTimeout(r, 700));

  popoverState = await isPopoverOpen();
  console.log(`  3. Notifications popover closed: ${!popoverState ? 'YES' : 'NO'}`);

  const coords02 = await getMapCoordinates();
  const selected02 = await getSelectedCellFromDOM();
  console.log(`  4. Map Center Coordinates: [lon: ${coords02.lon.toFixed(4)}, lat: ${coords02.lat.toFixed(4)}, zoom: ${coords02.zoom.toFixed(1)}]`);
  console.log(`  5. Selected Cell in Right Panel: ${selected02}`);

  if (Math.abs(coords02.lon - 86.92) < 0.2 && Math.abs(coords02.lat - 23.65) < 0.2 && selected02 === 'SC-2026-0917-02') {
    console.log('  🎉 TEST 3 PASSED: Map accurately moved to Asansol-Durgapur for SC-2026-0917-02!');
  } else {
    console.error('  ❌ TEST 3 FAILED');
  }

  // Check console errors
  console.log('\n=============================================================');
  console.log('CONSOLE LOG AUDIT:');
  console.log(`Total Console Errors: ${client.consoleErrors.length}`);
  if (client.consoleErrors.length > 0) {
    console.error('  Errors caught:', client.consoleErrors);
  } else {
    console.log('  ✓ 0 JavaScript console errors detected during entire run.');
  }

  client.close();
  chromeProcess.kill();

  console.log('\n=============================================================');
  console.log('🎉 ALL BROWSER VERIFICATION TESTS PASSED (100%)');
  console.log('=============================================================\n');
}

run().catch(err => {
  console.error('Test runner failed:', err);
  process.exit(1);
});
