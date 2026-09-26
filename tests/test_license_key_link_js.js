// "I have a license key" in the trial banner opened nothing (2026-09-26).
//
// The link calls shmShowLicense(), which only switched the self-host
// modal's step to 'license'. That is enough from INSIDE the modal, where
// the overlay is already up, but the banner fires it with the overlay
// still display:none — the step flipped behind a hidden parent and the
// link read as dead. shmShowLicense must raise the overlay itself.
//
// Runs under `node tests/test_license_key_link_js.js` — no jsdom, ~50ms.
// Loads the shipped onboarding.js against a stub DOM so it tests source.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SRC = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'onboarding.js');

let passed = 0;
let failed = 0;

function eq(actual, expected, label) {
  if (actual === expected) {
    passed++;
    console.log('  ok   ' + label);
  } else {
    failed++;
    console.log('  FAIL ' + label);
    console.log('       expected: ' + JSON.stringify(expected));
    console.log('       actual:   ' + JSON.stringify(actual));
  }
}

// The ids onboarding.js reaches for, as the dashboard serves them: the
// overlay starts hidden, every step starts hidden.
function makeDom() {
  const els = {};
  function el(id, display) {
    els[id] = { id: id, style: { display: display }, textContent: '',
                focus: function () { els[id].focused = true; } };
    return els[id];
  }
  el('selfhost-modal-overlay', 'none');
  ['home', 'otp', 'wait', 'license', 'ended'].forEach(function (s) {
    el('shm-step-' + s, 'none');
  });
  ['shm-home-error', 'shm-otp-error', 'shm-wait-error', 'shm-license-error']
    .forEach(function (id) { el(id, ''); });
  el('shm-tagline', '');
  el('shm-license-input', '');
  return els;
}

function load() {
  const els = makeDom();
  const sandbox = {
    document: {
      readyState: 'complete',
      getElementById: function (id) { return els[id] || null; },
      addEventListener: function () {},
    },
    setTimeout: function (fn) { fn(); return 0; },
    clearTimeout: function () {},
    setInterval: function () { return 0; },
    clearInterval: function () {},
    fetch: function () { return Promise.resolve({ json: function () { return {}; } }); },
    // CLOUD_MODE short-circuits _boot(): this suite is about the shm*
    // globals, not the first-run gate.
    CLOUD_MODE: true,
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(SRC, 'utf8'), sandbox);
  return { win: sandbox, els: els };
}

console.log('shmShowLicense — reachable from the banner, not just from inside the modal');

const cold = load();
eq(typeof cold.win.shmShowLicense, 'function', 'shmShowLicense is exported on window');
eq(cold.els['selfhost-modal-overlay'].style.display, 'none', 'overlay starts hidden');

cold.win.shmShowLicense();
eq(cold.els['selfhost-modal-overlay'].style.display, 'flex',
   'a cold call raises the overlay (this is the bug: it stayed none)');
eq(cold.els['shm-step-license'].style.display, 'block', 'the paste step is the visible step');
eq(cold.els['shm-step-home'].style.display, 'none', 'the sign-in step is hidden');
eq(cold.els['shm-license-input'].focused, true, 'the key field takes focus');

// From inside an already-open modal the behaviour is unchanged.
const warm = load();
warm.win.openSelfhostModal();
eq(warm.els['shm-step-home'].style.display, 'block', 'openSelfhostModal still lands on home');
warm.win.shmShowLicense();
eq(warm.els['selfhost-modal-overlay'].style.display, 'flex', 'overlay stays up');
eq(warm.els['shm-step-license'].style.display, 'block', 'in-modal link still switches step');

console.log('');
console.log(failed === 0 ? 'PASS (' + passed + ')' : 'FAIL (' + failed + ' of ' + (passed + failed) + ')');
process.exit(failed === 0 ? 0 : 1);
