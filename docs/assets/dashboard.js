/**
 * docs/assets/dashboard.js
 * DMMapp — Interactive Dashboard Logic
 * ─────────────────────────────────────────────────────────────────────────
 * CHANGES FROM STANDALONE VERSION:
 *  - initTheme() and all localStorage theme logic REMOVED.
 *    MkDocs Material owns the theme toggle natively via the palette config
 *    in mkdocs.yml. Dark mode is expressed via
 *    [data-md-color-scheme="slate"] on <body> — handled in dashboard.css.
 *  - fetch() path updated: 'data.json' → 'assets/data.json' to resolve
 *    correctly from the MkDocs-built root.
 *  - renderTable() no longer builds rows. hooks/library_pages.py writes one
 *    <tr data-record-id="…"> per record into the built index.html, so the
 *    directory is readable without JavaScript. renderTable() now reorders and
 *    detaches those rows, which keeps the row markup defined in one place.
 *  - Sort header aria-sort attribute is now toggled for a11y.
 *  - No global mutable state beyond allData/sort tracking inside the IIFE.
 * ─────────────────────────────────────────────────────────────────────────
 */

// Explicit, stable display order for the quantity filter: the enum's
// meaning ("how much is digitised") does not sort alphabetically.
const QUANTITY_ORDER = ['Few', 'Dozens', 'Hundreds', 'Thousands', 'Unknown'];

// Fixed column order for CSV/JSON export, matching schema.json's field
// list. Fixed rather than derived from the current result set, so a
// zero-record export still produces a correct header row.
const EXPORT_FIELDS = [
  'id', 'library', 'nation', 'city', 'website', 'copyright', 'quantity',
  'iiif', 'is_free_cultural_works_license', 'aggregators',
];

// Separates the aggregator memberships of one library inside the single
// CSV cell they share. CSV is flat, so the array is written as text; the
// JSON export carries the array itself and needs no such flattening.
const CSV_AGGREGATOR_SEPARATOR = '; ';

/**
 * Return a record's usable aggregator entries, in dataset order.
 *
 * An entry without a name is dropped, matching hooks/library_pages.py:
 * the name is what identifies the aggregator to a reader and to the filter.
 * @param {Object} record
 * @returns {Array<{name: string, url?: string}>}
 */
function aggregatorsOf(record) {
  const entries = record?.aggregators;
  if (!Array.isArray(entries)) return [];
  return entries.filter(entry => entry && String(entry.name ?? '').trim());
}

document$.subscribe(() => {
  if (!document.getElementById('loader')) return;
  /** @type {Array<Object>} */
  let allData = [];
  // The record set currently passed to renderTable(), kept in sync by
  // filterData() and initializeDashboard(), so export can read "what the
  // visitor sees now" without recomputing the filter predicate.
  /** @type {Array<Object>} */
  let currentFiltered = [];
  let sortColumn = /** @type {string|null} */ (null);
  let sortDirection = /** @type {'asc'|'desc'} */ ('asc');

  // ── DOM references ────────────────────────────────────────────────────
  const loader          = /** @type {HTMLElement} */ (document.getElementById('loader'));
  const tableBody       = /** @type {HTMLTableSectionElement} */ (document.getElementById('tableBody'));
  const emptyState      = /** @type {HTMLElement} */ (document.getElementById('emptyState'));
  const searchInput     = /** @type {HTMLInputElement} */ (document.getElementById('searchInput'));
  const nationSelect    = /** @type {HTMLSelectElement} */ (document.getElementById('nationSelect'));
  const projectSelect   = /** @type {HTMLSelectElement} */ (document.getElementById('projectSelect'));
  const quantitySelect  = /** @type {HTMLSelectElement} */ (document.getElementById('quantitySelect'));
  const copyrightSelect = /** @type {HTMLSelectElement} */ (document.getElementById('copyrightSelect'));
  const iiifCheck     = /** @type {HTMLInputElement} */ (document.getElementById('iiifCheck'));
  const freeCheck     = /** @type {HTMLInputElement} */ (document.getElementById('freeCheck'));
  const clearFiltersBtn = document.getElementById('clearFilters');
  const randomLibraryBtn = /** @type {HTMLButtonElement} */ (document.getElementById('randomLibraryBtn'));
  const filtersActiveBadge = document.getElementById('filtersActiveBadge');
  // Export controls and the "N libraries showing" count each appear twice —
  // once above the table, once below — so 700+ pre-rendered rows never put
  // them out of reach. Selecting by attribute/class rather than a second
  // hardcoded id lets both instances stay wired through one code path.
  const exportCsvBtns  = document.querySelectorAll('[data-export="csv"]');
  const exportJsonBtns = document.querySelectorAll('[data-export="json"]');

  // Stats spans
  const statTotal    = document.getElementById('statTotal');
  const statNations  = document.getElementById('statNations');
  const statIIIF     = document.getElementById('statIIIF');
  const statProjects = document.getElementById('statProjects');
  const showingCountEls = document.querySelectorAll('.js-showing-count');

  // ── Pre-rendered rows ─────────────────────────────────────────────────
  // The build writes one row per record into the page, so the table is
  // already complete before this script runs. Index those rows by record id
  // once; renderTable() then moves the ones a filter keeps and leaves the
  // rest detached, ready to come back when the filter changes.
  /** @type {Map<string, HTMLTableRowElement>} */
  const rowsById = new Map();
  tableBody.querySelectorAll('tr[data-record-id]').forEach(row => {
    rowsById.set(row.dataset.recordId, row);
  });

  // ── Data loading ──────────────────────────────────────────────────────
  // Path is relative to the MkDocs-built site root. The homepage is served
  // from the site root, so 'assets/data.json' resolves correctly on both
  // localhost (mkdocs serve) and GitHub Pages.
  /**
   * @param {string} path
   * @returns {Promise<any>}
   */
  function loadJson(path) {
    return fetch(path).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    });
  }

  loadJson('assets/data.json')
    .then(data => {
      allData = data.sort((a, b) => a.library.localeCompare(b.library));
      initializeDashboard();

      // Fade out loader
      loader.style.opacity = '0';
      loader.style.pointerEvents = 'none';
      setTimeout(() => loader.remove(), 400);
    })
    .catch(err => {
      showLoadError(err.message);
    });

  /**
   * Replace the loader with an error state, built from safe DOM APIs so a
   * fetch/parse error message is always shown as text, never parsed as HTML.
   * @param {string} message
   */
  function showLoadError(message) {
    const icon = document.createElement('i');
    icon.className = 'bi bi-exclamation-triangle';
    icon.setAttribute('aria-hidden', 'true');
    icon.style.fontSize = '3rem';
    icon.style.color = '#c62828';

    const text = document.createElement('p');
    text.style.color = '#c62828';
    text.style.marginTop = '.75rem';
    text.style.fontSize = '.875rem';
    text.append('Failed to load data.json', document.createElement('br'));

    const small = document.createElement('small');
    small.textContent = message;
    text.appendChild(small);

    loader.replaceChildren(icon, text);
  }

  // ── Bootstrap ─────────────────────────────────────────────────────────
  function initializeDashboard() {
    populateNationFilter();
    populateProjectFilter();
    populateQuantityFilter();
    populateCopyrightFilter();
    updateStats(allData);
    renderTable(allData);
    currentFiltered = allData; // no filter has run yet, so this is everything
    initializeSorting();
    // The dataset is only trustworthy once it has loaded, so the random-pick
    // and export controls are enabled here rather than at page load.
    if (randomLibraryBtn) randomLibraryBtn.disabled = false;
    exportCsvBtns.forEach(btn => { btn.disabled = false; });
    exportJsonBtns.forEach(btn => { btn.disabled = false; });
  }

  // ── Sorting ───────────────────────────────────────────────────────────
  function initializeSorting() {
    document.querySelectorAll('.sortable').forEach(th => {
      th.addEventListener('click', () => handleSort(th.dataset.sort, th));

      // Keyboard: Enter or Space activates sort
      th.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSort(th.dataset.sort, th);
        }
      });
    });
  }

  /**
   * @param {string} column
   * @param {HTMLElement} headerEl
   */
  function handleSort(column, headerEl) {
    // Toggle direction on same column, reset to 'asc' for a new column
    sortDirection = (sortColumn === column && sortDirection === 'asc') ? 'desc' : 'asc';
    sortColumn = column;

    // Reset all header states
    document.querySelectorAll('.sortable').forEach(th => {
      th.classList.remove('active');
      th.removeAttribute('data-sort-direction');
      th.setAttribute('aria-sort', 'none');
    });

    // Activate the clicked header
    headerEl.classList.add('active');
    headerEl.dataset.sortDirection = sortDirection;
    headerEl.setAttribute(
      'aria-sort',
      sortDirection === 'asc' ? 'ascending' : 'descending',
    );

    // Sort in place
    allData.sort((a, b) => {
      let va = a[column] ?? '';
      let vb = b[column] ?? '';
      if (typeof va === 'string') va = va.toLowerCase();
      if (typeof vb === 'string') vb = vb.toLowerCase();
      if (va < vb) return sortDirection === 'asc' ? -1 : 1;
      if (va > vb) return sortDirection === 'asc' ?  1 : -1;
      return 0;
    });

    filterData(); // re-apply current filters on the sorted data
  }

  // ── Render ────────────────────────────────────────────────────────────
  /**
   * Show the given records, in the given order, using the pre-rendered rows.
   *
   * Appending a row that is already in the document moves it, so this both
   * reorders and filters in one pass. A record with no pre-rendered row is
   * skipped: that can only happen if a cached data.json is newer than the
   * page, and dropping the row is safer than inventing markup for it.
   *
   * @param {Array<Object>} data
   */
  function renderTable(data) {
    const rows = data
      .map(item => rowsById.get(String(item.id)))
      .filter(Boolean);
    const tableScroll = document.querySelector('.table-scroll');

    if (rows.length === 0) {
      tableBody.replaceChildren();
      if (tableScroll) tableScroll.style.display = 'none';
      emptyState.hidden = false;
      showingCountEls.forEach(el => { el.textContent = '0'; });
      return;
    }

    if (tableScroll) tableScroll.style.display = '';
    emptyState.hidden = true;

    const frag = document.createDocumentFragment();
    rows.forEach(row => frag.appendChild(row));
    tableBody.replaceChildren(frag);

    showingCountEls.forEach(el => { el.textContent = String(rows.length); });
  }

  // ── Stats ─────────────────────────────────────────────────────────────
  /**
   * @param {Array<Object>} data
   */
  function updateStats(data) {
    if (statTotal)    statTotal.textContent    = String(data.length);
    if (statNations)  statNations.textContent  = String(new Set(data.map(d => d.nation)).size);
    if (statIIIF)     statIIIF.textContent     = String(data.filter(d => d.iiif).length);
    if (statProjects) {
      // Distinct aggregators across every membership, so a library counted
      // once per project it belongs to never inflates the total.
      const projects = new Set(data.flatMap(d => aggregatorsOf(d).map(a => a.name)));
      statProjects.textContent = String(projects.size);
    }
  }

  // ── Filter population ─────────────────────────────────────────────────
  function populateNationFilter() {
    const nations = [...new Set(allData.map(d => d.nation))].sort();
    nations.forEach(nation => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = nation;
      nationSelect.appendChild(opt);
    });
  }

  function populateProjectFilter() {
    const projects = [
      ...new Set(allData.flatMap(d => aggregatorsOf(d).map(a => a.name))),
    ].sort();

    projects.forEach(project => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = project;
      projectSelect.appendChild(opt);
    });
  }

  /**
   * Options follow QUANTITY_ORDER rather than the alphabetised values seen
   * in the data. A value present in the data but absent from that list
   * (a dataset drifted from schema.json's enum) is appended rather than
   * dropped, so it stays filterable instead of silently disappearing.
   */
  function populateQuantityFilter() {
    const present = new Set(allData.map(d => d.quantity).filter(Boolean));
    const known   = QUANTITY_ORDER.filter(q => present.has(q));
    const unknown = [...present].filter(q => !QUANTITY_ORDER.includes(q)).sort();

    [...known, ...unknown].forEach(quantity => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = quantity;
      quantitySelect.appendChild(opt);
    });
  }

  function populateCopyrightFilter() {
    const values = [...new Set(allData.map(d => d.copyright).filter(Boolean))].sort();
    values.forEach(copyright => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = copyright;
      copyrightSelect.appendChild(opt);
    });
  }

  // The four selects behind the "More filters" disclosure are collapsed by
  // default, so an active one among them would otherwise be invisible.
  // Counted separately from the always-visible search box and toggles,
  // which have no such visibility problem.
  function updateFiltersActiveBadge() {
    if (!filtersActiveBadge) return;
    const count = [nationSelect, projectSelect, quantitySelect, copyrightSelect]
      .filter(select => select.value !== 'All').length;
    filtersActiveBadge.textContent = String(count);
    filtersActiveBadge.hidden = count === 0;
  }

  // ── Filter engine ─────────────────────────────────────────────────────
  function filterData() {
    updateFiltersActiveBadge();

    const term      = searchInput.value.toLowerCase().trim();
    const nation    = nationSelect.value;
    const project   = projectSelect.value;
    const quantity  = quantitySelect.value;
    const copyright = copyrightSelect.value;
    const wantIIIF  = iiifCheck.checked;
    const wantFree  = freeCheck.checked;

    const filtered = allData.filter(d => {
      const names = aggregatorsOf(d).map(a => a.name);

      const matchSearch =
        !term ||
        d.library?.toLowerCase().includes(term) ||
        d.city?.toLowerCase().includes(term)    ||
        d.nation?.toLowerCase().includes(term)  ||
        names.some(name => name.toLowerCase().includes(term)) ||
        d.copyright?.toLowerCase().includes(term);

      const matchNation    = nation    === 'All' || d.nation === nation;
      // Any one membership is enough, so a library in several aggregators
      // appears under each of their filters.
      const matchProject   = project   === 'All' || names.includes(project);
      const matchQuantity  = quantity  === 'All' || d.quantity === quantity;
      const matchCopyright = copyright === 'All' || d.copyright === copyright;
      const matchIIIF      = !wantIIIF || d.iiif === true;
      const matchFree      = !wantFree || d.is_free_cultural_works_license === true;

      return matchSearch && matchNation && matchProject && matchQuantity &&
        matchCopyright && matchIIIF && matchFree;
    });

    currentFiltered = filtered;
    renderTable(filtered);
    updateStats(filtered);
  }

  // ── Export ────────────────────────────────────────────────────────────
  /**
   * A value a spreadsheet application would read as a formula (leading
   * =, +, -, @, tab, or carriage return) is prefixed with a single quote,
   * so it opens as literal text instead of being evaluated. See OWASP's
   * CSV injection guidance — this is publicly contributed data, so it must
   * be treated as untrusted the same way rendered HTML already is.
   * @param {string} value
   * @returns {string}
   */
  function neutraliseFormula(value) {
    return /^[=+\-@\t\r]/.test(value) ? `'${value}` : value;
  }

  /**
   * @param {*} value
   * @returns {string}
   */
  function csvField(value) {
    const text = neutraliseFormula(value == null ? '' : String(value));
    return /["\r\n,]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  /**
   * Return the value written to one CSV cell.
   *
   * Every field is scalar except aggregators, which is flattened to
   * "name (url)" per membership so the column stays readable in a
   * spreadsheet instead of becoming "[object Object]".
   * @param {Object} record
   * @param {string} field
   * @returns {*}
   */
  function exportValue(record, field) {
    if (field !== 'aggregators') return record[field];
    return aggregatorsOf(record)
      .map(a => (a.url ? `${a.name} (${a.url})` : a.name))
      .join(CSV_AGGREGATOR_SEPARATOR);
  }

  /**
   * @param {Array<Object>} records
   * @returns {string}
   */
  function toCsv(records) {
    const lines = [EXPORT_FIELDS.join(',')];
    records.forEach(record => {
      lines.push(EXPORT_FIELDS.map(field => csvField(exportValue(record, field))).join(','));
    });
    return lines.join('\r\n');
  }

  /**
   * Builds a Blob, triggers a download through a detached <a>, and revokes
   * the object URL immediately after — the link never needs to stay in the
   * document once the download has started.
   * @param {string} content
   * @param {string} filename
   * @param {string} mimeType
   */
  function downloadFile(content, filename, mimeType) {
    let url;
    try {
      url = URL.createObjectURL(new Blob([content], { type: mimeType }));
    } catch {
      // Blob/URL.createObjectURL can be missing or throw in a locked-down
      // environment; degrade to doing nothing rather than breaking the page.
      return;
    }

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  exportCsvBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      downloadFile(toCsv(currentFiltered), 'dmm-libraries.csv', 'text/csv;charset=utf-8');
    });
  });

  exportJsonBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      downloadFile(JSON.stringify(currentFiltered, null, 2), 'dmm-libraries.json', 'application/json');
    });
  });

  // ── Explore a random library ─────────────────────────────────────────
  // Draws from the full directory rather than the visitor's current filters:
  // this control exists for serendipitous discovery, so narrowing it to a
  // small or empty filtered view would undermine the point, and it would
  // otherwise need its own "no results" handling separate from filterData().
  /**
   * Return a randomly chosen record's page URL, read from that record's own
   * pre-rendered row rather than rebuilt from its dataset fields, so a
   * mismatch between data.json and the built page can never invent a URL
   * that no page actually exists at.
   * @returns {string|null}
   */
  function pickRandomLibraryUrl() {
    if (allData.length === 0) return null;
    const record = allData[Math.floor(Math.random() * allData.length)];
    const row = rowsById.get(String(record.id));
    const link = /** @type {HTMLAnchorElement|null} */ (row?.querySelector('a.library-name') ?? null);
    return link ? link.getAttribute('href') : null;
  }

  randomLibraryBtn?.addEventListener('click', () => {
    const url = pickRandomLibraryUrl();
    // window.open(url, '_self') rather than location.assign(url): both
    // navigate the current tab, but this leaves navigation on a property
    // that a test can stub instead of one the platform makes read-only.
    if (url) window.open(url, '_self');
  });

  // ── Event listeners ───────────────────────────────────────────────────
  searchInput.addEventListener('input', filterData);
  nationSelect.addEventListener('change', filterData);
  projectSelect.addEventListener('change', filterData);
  quantitySelect.addEventListener('change', filterData);
  copyrightSelect.addEventListener('change', filterData);
  iiifCheck.addEventListener('change', filterData);
  freeCheck.addEventListener('change', filterData);

  clearFiltersBtn?.addEventListener('click', () => {
    searchInput.value     = '';
    nationSelect.value    = 'All';
    projectSelect.value   = 'All';
    quantitySelect.value  = 'All';
    copyrightSelect.value = 'All';
    iiifCheck.checked     = false;
    freeCheck.checked     = false;
    filterData();
  });
});
