'use strict';

// Focused regression tests for docs/assets/dashboard.js's data-load error
// path. Runs the real script inside a jsdom window via node:test, so the
// assertions exercise production code rather than a reimplementation of it.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const SCRIPT_PATH = path.join(__dirname, 'dashboard.js');
const SCRIPT_SOURCE = fs.readFileSync(SCRIPT_PATH, 'utf8');

function baseHtml(rowsHtml) {
  return `
    <div id="dashboard-root">
      <div id="loader"></div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr><th class="sortable" data-sort="library" tabindex="0"></th></tr>
          </thead>
          <tbody id="tableBody">${rowsHtml}</tbody>
        </table>
      </div>
      <div id="emptyState" hidden></div>
      <input id="searchInput">
      <select id="nationSelect"><option value="All">All</option></select>
      <select id="projectSelect"><option value="All">All</option></select>
      <input id="iiifCheck" type="checkbox">
      <input id="freeCheck" type="checkbox">
      <button id="clearFilters"></button>
      <button disabled id="randomLibraryBtn"></button>
      <span id="statTotal"></span>
      <span id="statNations"></span>
      <span id="statIIIF"></span>
      <span id="statProjects"></span>
      <span id="showingCount"></span>
    </div>
  `;
}

// Loads the real dashboard.js into a fresh jsdom window. `runScripts:
// "outside-only"` keeps any <script> in the fixture HTML from running
// automatically; window.eval() is then used to run the real file ourselves.
function loadDashboard({ rowsHtml = '', fetchImpl }) {
  const dom = new JSDOM(baseHtml(rowsHtml), {
    runScripts: 'outside-only',
    url: 'https://example.invalid/',
  });
  const { window } = dom;
  window.document$ = { subscribe: (fn) => fn() };
  window.fetch = fetchImpl;
  window.eval(SCRIPT_SOURCE);
  return dom;
}

// One microtask-queue drain is enough: Node fully empties the microtask
// queue, including microtasks enqueued while draining, before running a
// scheduled timer callback.
function flushMicrotasks() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

test('a rejected fetch renders its error message as text, not as parsed HTML', async () => {
  const maliciousMessage = '<img src=x onerror="window.__pwned = true">';
  const dom = loadDashboard({
    fetchImpl: () => Promise.reject(new Error(maliciousMessage)),
  });

  await flushMicrotasks();

  const { window } = dom;
  const loader = window.document.getElementById('loader');

  assert.equal(loader.querySelector('img'), null, 'the error message must not be parsed into an <img> element');
  assert.ok(loader.textContent.includes(maliciousMessage), 'the error message must still be visible as text');
  assert.equal(window.__pwned, undefined, 'no injected handler must have executed');
});

test('an HTTP error status renders its status text as text, not as parsed HTML', async () => {
  const dom = loadDashboard({
    fetchImpl: () =>
      Promise.resolve({
        ok: false,
        status: 500,
        statusText: '<script>window.__pwned = true</script>',
      }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const loader = window.document.getElementById('loader');

  assert.equal(loader.querySelector('script'), null);
  assert.ok(loader.textContent.includes('HTTP 500'));
  assert.equal(window.__pwned, undefined);
});

test('regression guard: pre-rendered rows still load, sort, and update stats on success', async () => {
  const data = [
    { id: 2, library: 'Beta Library', nation: 'Nation B', city: 'City B', iiif: false, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="2"><td>Beta Library</td><td>Nation B</td><td></td><td></td></tr>
      <tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>
    `,
    fetchImpl: (requestedPath) => {
      assert.match(String(requestedPath), /data\.json$/);
      return Promise.resolve({ ok: true, json: () => Promise.resolve(data) });
    },
  });

  await flushMicrotasks();

  const { window } = dom;
  const rows = [...window.document.querySelectorAll('#tableBody tr')];

  assert.equal(rows.length, 2);
  // allData.sort() by library.localeCompare puts Alpha before Beta.
  assert.equal(rows[0].dataset.recordId, '1');
  assert.equal(rows[1].dataset.recordId, '2');
  assert.equal(window.document.getElementById('statTotal').textContent, '2');
  assert.equal(window.document.getElementById('emptyState').hidden, true);
  assert.equal(
    window.document.getElementById('randomLibraryBtn').disabled,
    false,
    'the random-library control must be enabled once the dataset has loaded',
  );
});

test('load failure: the random-library control stays disabled and does not navigate', async () => {
  const dom = loadDashboard({
    fetchImpl: () => Promise.reject(new Error('network down')),
  });

  await flushMicrotasks();

  const { window } = dom;
  const randomLibraryBtn = window.document.getElementById('randomLibraryBtn');
  const navigations = [];
  window.open = (url) => navigations.push(url);

  assert.equal(randomLibraryBtn.disabled, true);
  randomLibraryBtn.click();
  assert.deepEqual(navigations, [], 'a disabled control must not navigate anywhere');
});

test('random library: happy path navigates to a real record URL from its pre-rendered row', async () => {
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
    { id: 2, library: 'Beta Library', nation: 'Nation B', city: 'City B', iiif: false, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td><a class="library-name" href="libraries/alpha-library-1/">Alpha Library</a></td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td><a class="library-name" href="libraries/beta-library-2/">Beta Library</a></td><td>Nation B</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  // Deterministic pick: Math.random() * 2 → floor(0) selects allData[0], the
  // first record after the library.localeCompare sort (Alpha).
  window.Math.random = () => 0;
  const navigations = [];
  window.open = (url) => navigations.push(url);

  window.document.getElementById('randomLibraryBtn').click();

  assert.deepEqual(navigations, ['libraries/alpha-library-1/']);
});

test('random library: the target comes from the pre-rendered row, never rebuilt from dataset fields', async () => {
  // A library name that a naive JS slugify would mangle differently from the
  // Python build. The href on the pre-rendered row is what the build
  // actually generated, and is deliberately not derivable from the name.
  const data = [
    { id: 7, library: 'Bibliothèque Ñoño & Co. <script>', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="7"><td><a class="library-name" href="libraries/bibliotheque-nono-and-co-7/">Bibliothèque Ñoño &amp; Co. &lt;script&gt;</a></td><td>Nation A</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  window.Math.random = () => 0;
  const navigations = [];
  window.open = (url) => navigations.push(url);

  window.document.getElementById('randomLibraryBtn').click();

  assert.deepEqual(navigations, ['libraries/bibliotheque-nono-and-co-7/']);
});

test('random library: a record with no matching pre-rendered row produces no navigation', async () => {
  // rowsById is built only from rows actually present in the page, so a
  // record present in data.json but missing its row (a stale cache) has
  // nothing to resolve to.
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
  ];

  const dom = loadDashboard({
    rowsHtml: '',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  window.Math.random = () => 0;
  const navigations = [];
  window.open = (url) => navigations.push(url);

  window.document.getElementById('randomLibraryBtn').click();

  assert.deepEqual(navigations, [], 'no row means no derivable URL, so nothing must be navigated to');
});

test('random library: an empty dataset does not throw and does not navigate', async () => {
  const dom = loadDashboard({
    rowsHtml: '',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve([]) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const navigations = [];
  window.open = (url) => navigations.push(url);

  assert.doesNotThrow(() => window.document.getElementById('randomLibraryBtn').click());
  assert.deepEqual(navigations, []);
});

test('random library: repeated activations can select different records', async () => {
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
    { id: 2, library: 'Beta Library', nation: 'Nation B', city: 'City B', iiif: false, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td><a class="library-name" href="libraries/alpha-library-1/">Alpha Library</a></td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td><a class="library-name" href="libraries/beta-library-2/">Beta Library</a></td><td>Nation B</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const navigations = [];
  window.open = (url) => navigations.push(url);
  const randomLibraryBtn = window.document.getElementById('randomLibraryBtn');

  window.Math.random = () => 0;
  randomLibraryBtn.click();
  window.Math.random = () => 0.99;
  randomLibraryBtn.click();

  assert.deepEqual(navigations, ['libraries/alpha-library-1/', 'libraries/beta-library-2/']);
});
