'use strict';

// Focused regression tests for docs/assets/dashboard.js's data-load error
// path. Runs the real script inside a jsdom window via node:test, so the
// assertions exercise production code rather than a reimplementation of it.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');

const SCRIPT_PATH = path.join(__dirname, 'dashboard.js');
const SCRIPT_SOURCE = fs.readFileSync(SCRIPT_PATH, 'utf8');

// jsdom doesn't implement the `download` attribute, so clicking the export
// anchor triggers its "Not implemented: navigation" warning even though the
// click itself does exactly what production code intends. Routing jsdom's
// own diagnostic errors through omitJSDOMErrors keeps that expected noise
// out of test output without hiding a genuine console message from the page.
const virtualConsole = new VirtualConsole();
virtualConsole.sendTo(console, { omitJSDOMErrors: true });

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
      <select id="quantitySelect"><option value="All">All</option></select>
      <select id="copyrightSelect"><option value="All">All</option></select>
      <span hidden id="filtersActiveBadge">0</span>
      <input id="iiifCheck" type="checkbox">
      <input id="freeCheck" type="checkbox">
      <button id="clearFilters"></button>
      <button disabled id="randomLibraryBtn"></button>
      <button data-export="csv" disabled id="exportCsvBtnTop"></button>
      <button data-export="json" disabled id="exportJsonBtnTop"></button>
      <button data-export="csv" disabled id="exportCsvBtn"></button>
      <button data-export="json" disabled id="exportJsonBtn"></button>
      <span id="statTotal"></span>
      <span id="statNations"></span>
      <span id="statIIIF"></span>
      <span id="statProjects"></span>
      <span class="js-showing-count" id="showingCountTop"></span>
      <span class="js-showing-count" id="showingCount"></span>
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
    virtualConsole,
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

// jsdom's Blob has no .text()/.arrayBuffer(), so content can't be read back
// off a real Blob instance. Overriding window.Blob to a plain capturing
// constructor — rather than trying to unwrap jsdom's Blob — is what lets a
// test see the exact string dashboard.js handed to `new Blob([content])`.
// window.URL.createObjectURL/revokeObjectURL are stubbed alongside it so no
// test depends on jsdom's (partial) real implementation of either.
function stubDownloads(window) {
  const downloads = [];
  window.Blob = function (parts, opts) {
    this.__content = parts.join('');
    this.__type = opts && opts.type;
  };
  window.URL.createObjectURL = (blob) => {
    downloads.push({ content: blob.__content, type: blob.__type });
    return 'blob:stub';
  };
  window.URL.revokeObjectURL = () => {};
  return downloads;
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

test('quantity and copyright filters: options follow the declared order and narrow the results', async () => {
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Few', copyright: 'Public Domain Mark 1.0' },
    { id: 2, library: 'Beta Library', nation: 'Nation B', city: 'City B', iiif: false, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Thousands', copyright: 'CC BY-NC 4.0' },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td>Beta Library</td><td>Nation B</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const quantitySelect = window.document.getElementById('quantitySelect');
  const copyrightSelect = window.document.getElementById('copyrightSelect');

  // QUANTITY_ORDER, not alphabetical: 'Few' before 'Thousands' even though
  // alphabetising would put 'Thousands' first.
  assert.deepEqual([...quantitySelect.options].map(o => o.value), ['All', 'Few', 'Thousands']);
  // Copyright has no declared order, so it is alphabetised like nation/project.
  assert.deepEqual([...copyrightSelect.options].map(o => o.value), ['All', 'CC BY-NC 4.0', 'Public Domain Mark 1.0']);

  quantitySelect.value = 'Few';
  quantitySelect.dispatchEvent(new window.Event('change'));

  let rows = [...window.document.querySelectorAll('#tableBody tr')];
  assert.deepEqual(rows.map(r => r.dataset.recordId), ['1']);
  assert.equal(window.document.getElementById('showingCount').textContent, '1');

  quantitySelect.value = 'All';
  quantitySelect.dispatchEvent(new window.Event('change'));
  copyrightSelect.value = 'CC BY-NC 4.0';
  copyrightSelect.dispatchEvent(new window.Event('change'));

  rows = [...window.document.querySelectorAll('#tableBody tr')];
  assert.deepEqual(rows.map(r => r.dataset.recordId), ['2']);
});

test('quantity filter: a value outside the known enum is appended, and an empty copyright does not throw', async () => {
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Few', copyright: 'Public Domain Mark 1.0' },
    { id: 2, library: 'Zeta Library', nation: 'Nation Z', city: 'City Z', iiif: false, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Millions', copyright: '' },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td>Zeta Library</td><td>Nation Z</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  // 'Millions' is not in QUANTITY_ORDER, so it must not be dropped — it is
  // appended after the known values instead.
  assert.deepEqual(
    [...window.document.getElementById('quantitySelect').options].map(o => o.value),
    ['All', 'Few', 'Millions'],
  );

  const rows = [...window.document.querySelectorAll('#tableBody tr')];
  assert.equal(rows.length, 2, 'a record with an empty copyright must still be shown unfiltered');
});

test('copyright filter: a value containing markup becomes a plain option label, never injected markup', async () => {
  const maliciousCopyright = '<img src=x onerror="window.__pwned = true"> "quoted"';
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Few', copyright: maliciousCopyright },
  ];

  const dom = loadDashboard({
    rowsHtml: '<tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const copyrightSelect = window.document.getElementById('copyrightSelect');
  const option = [...copyrightSelect.options].find(o => o.value !== 'All');

  assert.equal(copyrightSelect.querySelector('img'), null, 'no element must be injected into the select');
  assert.equal(option.textContent, maliciousCopyright, 'the raw value must still be usable as an option label');
  assert.equal(window.__pwned, undefined);

  copyrightSelect.value = maliciousCopyright;
  copyrightSelect.dispatchEvent(new window.Event('change'));

  const rows = [...window.document.querySelectorAll('#tableBody tr')];
  assert.deepEqual(rows.map(r => r.dataset.recordId), ['1']);
});

test('load failure: the quantity and copyright filters stay seeded with only their default option', async () => {
  const dom = loadDashboard({
    fetchImpl: () => Promise.reject(new Error('network down')),
  });

  await flushMicrotasks();

  const { window } = dom;
  assert.deepEqual(
    [...window.document.getElementById('quantitySelect').options].map(o => o.value),
    ['All'],
  );
  assert.deepEqual(
    [...window.document.getElementById('copyrightSelect').options].map(o => o.value),
    ['All'],
  );
});

test('quantity and copyright filters compose with search, nation, project, and the toggles', async () => {
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: true, is_part_of: true, is_part_of_project_name: 'Project X', quantity: 'Few', copyright: 'Public Domain Mark 1.0' },
    { id: 2, library: 'Alpha Annex', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: true, is_part_of: true, is_part_of_project_name: 'Project X', quantity: 'Thousands', copyright: 'Public Domain Mark 1.0' },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td>Alpha Annex</td><td>Nation A</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const searchInput      = window.document.getElementById('searchInput');
  const nationSelect     = window.document.getElementById('nationSelect');
  const projectSelect    = window.document.getElementById('projectSelect');
  const quantitySelect   = window.document.getElementById('quantitySelect');
  const copyrightSelect  = window.document.getElementById('copyrightSelect');
  const iiifCheck        = window.document.getElementById('iiifCheck');
  const freeCheck        = window.document.getElementById('freeCheck');

  searchInput.value = 'alpha';
  searchInput.dispatchEvent(new window.Event('input'));
  nationSelect.value = 'Nation A';
  nationSelect.dispatchEvent(new window.Event('change'));
  projectSelect.value = 'Project X';
  projectSelect.dispatchEvent(new window.Event('change'));
  copyrightSelect.value = 'Public Domain Mark 1.0';
  copyrightSelect.dispatchEvent(new window.Event('change'));
  iiifCheck.checked = true;
  iiifCheck.dispatchEvent(new window.Event('change'));
  freeCheck.checked = true;
  freeCheck.dispatchEvent(new window.Event('change'));
  quantitySelect.value = 'Few';
  quantitySelect.dispatchEvent(new window.Event('change'));

  let rows = [...window.document.querySelectorAll('#tableBody tr')];
  assert.deepEqual(rows.map(r => r.dataset.recordId), ['1'], 'the intersection of every active filter must be record 1 only');

  quantitySelect.value = 'Thousands';
  quantitySelect.dispatchEvent(new window.Event('change'));

  rows = [...window.document.querySelectorAll('#tableBody tr')];
  assert.deepEqual(rows.map(r => r.dataset.recordId), ['2'], 'switching quantity alone must switch which record matches');

  searchInput.value = 'no such library';
  searchInput.dispatchEvent(new window.Event('input'));

  rows = [...window.document.querySelectorAll('#tableBody tr')];
  assert.equal(rows.length, 0);
  assert.equal(window.document.getElementById('emptyState').hidden, false);
});

test('clearFilters resets the quantity and copyright filters along with the rest', async () => {
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Few', copyright: 'Public Domain Mark 1.0' },
    { id: 2, library: 'Beta Library', nation: 'Nation B', city: 'City B', iiif: false, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Thousands', copyright: 'CC BY-NC 4.0' },
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td>Beta Library</td><td>Nation B</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const quantitySelect = window.document.getElementById('quantitySelect');
  const copyrightSelect = window.document.getElementById('copyrightSelect');

  quantitySelect.value = 'Few';
  quantitySelect.dispatchEvent(new window.Event('change'));
  copyrightSelect.value = 'Public Domain Mark 1.0';
  copyrightSelect.dispatchEvent(new window.Event('change'));

  assert.equal([...window.document.querySelectorAll('#tableBody tr')].length, 1);

  window.document.getElementById('clearFilters').click();

  assert.equal(quantitySelect.value, 'All');
  assert.equal(copyrightSelect.value, 'All');
  assert.equal([...window.document.querySelectorAll('#tableBody tr')].length, 2);
});

test('filters-active badge: hidden with none active, counts only the four collapsed selects, and resets on clearFilters', async () => {
  const data = [
    { id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A', iiif: true, is_free_cultural_works_license: false, is_part_of: false, is_part_of_project_name: null, quantity: 'Few', copyright: 'Public Domain Mark 1.0' },
  ];

  const dom = loadDashboard({
    rowsHtml: '<tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const badge = window.document.getElementById('filtersActiveBadge');
  const nationSelect    = window.document.getElementById('nationSelect');
  const quantitySelect  = window.document.getElementById('quantitySelect');
  const copyrightSelect = window.document.getElementById('copyrightSelect');
  const searchInput     = window.document.getElementById('searchInput');
  const iiifCheck       = window.document.getElementById('iiifCheck');

  assert.equal(badge.hidden, true, 'no filter is active on load, so the badge must stay hidden');

  // The always-visible search box and IIIF toggle are not among the four
  // collapsed selects, so activating them must not move the badge.
  searchInput.value = 'alpha';
  searchInput.dispatchEvent(new window.Event('input'));
  iiifCheck.checked = true;
  iiifCheck.dispatchEvent(new window.Event('change'));
  assert.equal(badge.hidden, true, 'search and the toggles are always visible and must not be counted');

  nationSelect.value = 'Nation A';
  nationSelect.dispatchEvent(new window.Event('change'));
  assert.equal(badge.hidden, false);
  assert.equal(badge.textContent, '1');

  quantitySelect.value = 'Few';
  quantitySelect.dispatchEvent(new window.Event('change'));
  copyrightSelect.value = 'Public Domain Mark 1.0';
  copyrightSelect.dispatchEvent(new window.Event('change'));
  assert.equal(badge.textContent, '3');

  window.document.getElementById('clearFilters').click();
  assert.equal(badge.hidden, true, 'clearFilters must reset the count back to zero');
  assert.equal(badge.textContent, '0');
});

const EXPORT_CSV_HEADER = 'id,library,nation,city,website,copyright,quantity,iiif,is_free_cultural_works_license,is_part_of,is_part_of_project_name,is_part_of_url';

function makeRecord(overrides) {
  return Object.assign({
    id: 1, library: 'Alpha Library', nation: 'Nation A', city: 'City A',
    website: 'https://alpha.example', copyright: 'CC0 1.0', quantity: 'Few',
    iiif: true, is_free_cultural_works_license: true, is_part_of: false,
    is_part_of_project_name: null, is_part_of_url: null,
  }, overrides);
}

test('load failure: every export control instance stays disabled', async () => {
  const dom = loadDashboard({
    fetchImpl: () => Promise.reject(new Error('network down')),
  });

  await flushMicrotasks();

  const { window } = dom;
  assert.equal(window.document.getElementById('exportCsvBtn').disabled, true);
  assert.equal(window.document.getElementById('exportJsonBtn').disabled, true);
  assert.equal(window.document.getElementById('exportCsvBtnTop').disabled, true);
  assert.equal(window.document.getElementById('exportJsonBtnTop').disabled, true);
});

test('duplicated controls: the top and bottom export buttons and showing-count spans stay in sync', async () => {
  const data = [
    makeRecord({ id: 1, library: 'Alpha Library', nation: 'Nation A' }),
    makeRecord({ id: 2, library: 'Beta Library', nation: 'Nation B' }),
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td>Beta Library</td><td>Nation B</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const doc = window.document;

  // Both instances of each control must be enabled the moment data loads.
  assert.equal(doc.getElementById('exportCsvBtnTop').disabled, false);
  assert.equal(doc.getElementById('exportJsonBtnTop').disabled, false);

  // Narrowing the result set must update both showing-count spans, not just
  // the one below the table.
  const nationSelect = doc.getElementById('nationSelect');
  nationSelect.value = 'Nation A';
  nationSelect.dispatchEvent(new window.Event('change'));
  assert.equal(doc.getElementById('showingCountTop').textContent, '1');
  assert.equal(doc.getElementById('showingCount').textContent, '1');

  // Clicking the TOP button — not just the established bottom one — must
  // trigger a real export, proving both are wired through the same handler.
  const downloads = stubDownloads(window);
  doc.getElementById('exportCsvBtnTop').click();

  assert.equal(downloads.length, 1);
  assert.ok(downloads[0].content.includes('Alpha Library'));
  assert.ok(!downloads[0].content.includes('Beta Library'));
});

test('export: CSV and JSON reflect the currently filtered records, not the full dataset', async () => {
  const data = [
    makeRecord({ id: 1, library: 'Alpha Library', nation: 'Nation A' }),
    makeRecord({ id: 2, library: 'Beta Library', nation: 'Nation B' }),
  ];

  const dom = loadDashboard({
    rowsHtml: `
      <tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>
      <tr data-record-id="2"><td>Beta Library</td><td>Nation B</td><td></td><td></td></tr>
    `,
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const downloads = stubDownloads(window);

  const nationSelect = window.document.getElementById('nationSelect');
  nationSelect.value = 'Nation A';
  nationSelect.dispatchEvent(new window.Event('change'));

  window.document.getElementById('exportCsvBtn').click();
  window.document.getElementById('exportJsonBtn').click();

  assert.equal(downloads.length, 2);
  const [csvDownload, jsonDownload] = downloads;
  assert.equal(csvDownload.type, 'text/csv;charset=utf-8');
  assert.equal(jsonDownload.type, 'application/json');

  const csvLines = csvDownload.content.split('\r\n');
  assert.equal(csvLines.length, 2, 'header row plus exactly one data row for the filtered record');
  assert.equal(csvLines[0], EXPORT_CSV_HEADER);
  assert.ok(csvLines[1].includes('Alpha Library'));
  assert.ok(!csvDownload.content.includes('Beta Library'), 'the filtered-out record must not appear in the export');

  assert.deepEqual(JSON.parse(jsonDownload.content), [data[0]]);
});

test('export CSV: commas, quotes, and newlines are quoted so the row still parses correctly', async () => {
  const data = [makeRecord({ library: 'Alpha, "The" Library\nSecond line' })];

  const dom = loadDashboard({
    rowsHtml: '<tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const downloads = stubDownloads(window);
  window.document.getElementById('exportCsvBtn').click();

  // RFC 4180: the field is quoted, and its embedded double quotes are doubled.
  assert.ok(downloads[0].content.includes('"Alpha, ""The"" Library\nSecond line"'));
});

test('export CSV: a value beginning with a formula character is neutralised as text', async () => {
  const data = [makeRecord({ library: "=cmd|' /C calc'!A1", copyright: '+1' })];

  const dom = loadDashboard({
    rowsHtml: '<tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const downloads = stubDownloads(window);
  window.document.getElementById('exportCsvBtn').click();

  const csv = downloads[0].content;
  assert.ok(csv.includes("'=cmd"), 'a leading = must be prefixed with a single quote so it opens as text');
  assert.ok(csv.includes("'+1"), 'a leading + must also be neutralised');
});

test('export: if URL.createObjectURL throws, the page stays interactive and nothing leaks into the DOM', async () => {
  const data = [makeRecord()];

  const dom = loadDashboard({
    rowsHtml: '<tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  window.URL.createObjectURL = () => { throw new Error('blocked'); };

  assert.doesNotThrow(() => window.document.getElementById('exportCsvBtn').click());
  assert.equal(window.document.querySelectorAll('#tableBody tr').length, 1, 'the table must remain intact');
  assert.equal(window.document.querySelector('a[download]'), null, 'no leftover download link should remain in the document');
});

test('export: a zero-match filter still produces a header-only CSV and an empty JSON array, and revokes the object URL', async () => {
  const data = [makeRecord()];

  const dom = loadDashboard({
    rowsHtml: '<tr data-record-id="1"><td>Alpha Library</td><td>Nation A</td><td></td><td></td></tr>',
    fetchImpl: () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  });

  await flushMicrotasks();

  const { window } = dom;
  const downloads = stubDownloads(window);
  let revokedCount = 0;
  window.URL.revokeObjectURL = () => { revokedCount++; };

  const searchInput = window.document.getElementById('searchInput');
  searchInput.value = 'no such library';
  searchInput.dispatchEvent(new window.Event('input'));

  window.document.getElementById('exportCsvBtn').click();
  window.document.getElementById('exportJsonBtn').click();

  assert.equal(downloads[0].content, EXPORT_CSV_HEADER, 'header only, no data rows');
  assert.equal(downloads[1].content, '[]');
  assert.equal(revokedCount, 2, 'each export must revoke its own object URL');
});
