import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const localesDir = path.join(__dirname, 'locales');
const enPath = path.join(localesDir, 'en.json');

if (!fs.existsSync(enPath)) {
  console.error('❌ Canonical en.json not found at:', enPath);
  process.exit(1);
}

const en = JSON.parse(fs.readFileSync(enPath, 'utf8'));

function flatten(obj, prefix = '') {
  const flat = {};
  for (const k of Object.keys(obj)) {
    const val = obj[k];
    const fullKey = prefix ? `${prefix}.${k}` : k;
    if (val && typeof val === 'object' && !Array.isArray(val)) {
      Object.assign(flat, flatten(val, fullKey));
    } else {
      flat[fullKey] = val;
    }
  }
  return flat;
}

const enFlat = flatten(en);
const enKeys = Object.keys(enFlat);
const enKeySet = new Set(enKeys);

console.log('==================================================');
console.log('STORMTRACE i18n Translation Schema Validation');
console.log('==================================================');
console.log(`Canonical schema (en.json): ${enKeys.length} keys defined.\n`);

const localeFiles = fs.readdirSync(localesDir).filter(f => f.endsWith('.json') && f !== 'en.json');

let totalMissing = 0;
let totalExtra = 0;
let totalEmpty = 0;
let totalInterpolationErrors = 0;
let failedLocales = [];

const interpolationRegex = /\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g;

function getInterpolations(str) {
  if (typeof str !== 'string') return [];
  const matches = [];
  let m;
  while ((m = interpolationRegex.exec(str)) !== null) {
    matches.push(m[1]);
  }
  return matches.sort();
}

for (const file of localeFiles) {
  const code = file.replace('.json', '');
  const filePath = path.join(localesDir, file);
  let loc;
  try {
    loc = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    console.error(`❌ [${code}] Malformed JSON: ${err.message}`);
    process.exit(1);
  }

  const locFlat = flatten(loc);
  const locKeys = Object.keys(locFlat);
  const locKeySet = new Set(locKeys);

  const missing = enKeys.filter(k => !locKeySet.has(k));
  const extra = locKeys.filter(k => !enKeySet.has(k));
  const empty = locKeys.filter(k => locFlat[k] === null || locFlat[k] === undefined || String(locFlat[k]).trim() === '');
  
  // Check interpolation variables
  const interpErrors = [];
  for (const k of enKeys) {
    if (locFlat[k] !== undefined) {
      const enVars = getInterpolations(enFlat[k]);
      const locVars = getInterpolations(locFlat[k]);
      if (enVars.join(',') !== locVars.join(',')) {
        interpErrors.push({ key: k, enVars, locVars });
      }
    }
  }

  totalMissing += missing.length;
  totalExtra += extra.length;
  totalEmpty += empty.length;
  totalInterpolationErrors += interpErrors.length;

  const pct = ((locKeys.length - missing.length) / enKeys.length * 100).toFixed(0);

  if (missing.length === 0 && extra.length === 0 && empty.length === 0 && interpErrors.length === 0) {
    console.log(`✓ ${code}: ${pct}% schema (${locKeys.length}/${enKeys.length} keys) — PASS`);
  } else {
    console.log(`✗ ${code}: ${pct}% schema (${locKeys.length}/${enKeys.length} keys) — FAIL`);
    if (missing.length > 0) {
      console.log(`    Missing (${missing.length}):`, missing.slice(0, 5));
    }
    if (extra.length > 0) {
      console.log(`    Extra (${extra.length}):`, extra.slice(0, 5));
    }
    if (empty.length > 0) {
      console.log(`    Empty (${empty.length}):`, empty.slice(0, 5));
    }
    if (interpErrors.length > 0) {
      console.log(`    Interpolation mismatches (${interpErrors.length}):`, interpErrors.slice(0, 3));
    }
    failedLocales.push(code);
  }
}

console.log('\n--------------------------------------------------');
console.log(`Summary:`);
console.log(`Total Configured Locales: ${localeFiles.length + 1} (en + ${localeFiles.map(f => f.replace('.json', '')).join(', ')})`);
console.log(`Total Canonical Keys:    ${enKeys.length}`);
console.log(`Missing Keys:            ${totalMissing}`);
console.log(`Extra Keys:              ${totalExtra}`);
console.log(`Empty Values:            ${totalEmpty}`);
console.log(`Interpolation Mismatches:${totalInterpolationErrors}`);
console.log('--------------------------------------------------');

if (totalMissing === 0 && totalExtra === 0 && totalEmpty === 0 && totalInterpolationErrors === 0) {
  console.log('🎉 I18N VALIDATION PASSED — All configured locales are 100% compliant!');
  process.exit(0);
} else {
  console.error(`❌ I18N VALIDATION FAILED — ${failedLocales.join(', ')} have schema errors.`);
  process.exit(1);
}
