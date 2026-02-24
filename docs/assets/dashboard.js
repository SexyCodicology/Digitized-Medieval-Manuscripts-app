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
 *  - renderTable() updated to use new BEM class names (badge--, btn-visit,
 *    library-name, location-*, sort-icon--*).
 *  - Sort header aria-sort attribute is now toggled for a11y.
 *  - No global mutable state beyond allData/sort tracking inside the IIFE.
 * ─────────────────────────────────────────────────────────────────────────
 */

document$.subscribe(() => {
  if (!document.getElementById('loader')) return;
  /** @type {Array<Object>} */
  let allData = [];
  let sortColumn = /** @type {string|null} */ (null);
  let sortDirection = /** @type {'asc'|'desc'} */ ('asc');

  // ── DOM references ────────────────────────────────────────────────────
  const loader        = /** @type {HTMLElement} */ (document.getElementById('loader'));
  const tableBody     = /** @type {HTMLTableSectionElement} */ (document.getElementById('tableBody'));
  const emptyState    = /** @type {HTMLElement} */ (document.getElementById('emptyState'));
  const searchInput   = /** @type {HTMLInputElement} */ (document.getElementById('searchInput'));
  const nationSelect  = /** @type {HTMLSelectElement} */ (document.getElementById('nationSelect'));
  const projectSelect = /** @type {HTMLSelectElement} */ (document.getElementById('projectSelect'));
  const iiifCheck     = /** @type {HTMLInputElement} */ (document.getElementById('iiifCheck'));
  const freeCheck     = /** @type {HTMLInputElement} */ (document.getElementById('freeCheck'));
  const clearFiltersBtn = document.getElementById('clearFilters');

  // Stats spans
  const statTotal    = document.getElementById('statTotal');
  const statNations  = document.getElementById('statNations');
  const statIIIF     = document.getElementById('statIIIF');
  const statProjects = document.getElementById('statProjects');
  const showingCount = document.getElementById('showingCount');

  // ── Data loading ──────────────────────────────────────────────────────
  // Path is relative to the MkDocs-built site root. The homepage is served
  // from the site root, so 'assets/data.json' resolves correctly on both
  // localhost (mkdocs serve) and GitHub Pages.
  fetch('assets/data.json')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      allData = data.sort((a, b) => a.library.localeCompare(b.library));
      initializeDashboard();

      // Fade out loader
      loader.style.opacity = '0';
      loader.style.pointerEvents = 'none';
      setTimeout(() => loader.remove(), 400);
    })
    .catch(err => {
      loader.innerHTML = `
        <i class="bi bi-exclamation-triangle"
           style="font-size:3rem;color:#c62828;"
           aria-hidden="true"></i>
        <p style="color:#c62828;margin-top:.75rem;font-size:.875rem">
          Failed to load data.json<br>
          <small>${err.message}</small>
        </p>`;
    });

  // ── Bootstrap ─────────────────────────────────────────────────────────
  function initializeDashboard() {
    populateNationFilter();
    populateProjectFilter();
    updateStats(allData);
    renderTable(allData);
    initializeSorting();
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
   * Render the filtered/sorted dataset into the table.
   * @param {Array<Object>} data
   */
  function renderTable(data) {
    tableBody.innerHTML = '';
    const tableScroll = document.querySelector('.table-scroll');

    if (data.length === 0) {
      if (tableScroll) tableScroll.style.display = 'none';
      emptyState.hidden = false;
      if (showingCount) showingCount.textContent = '0';
      return;
    }

    if (tableScroll) tableScroll.style.display = '';
    emptyState.hidden = true;

    const frag = document.createDocumentFragment();

    data.forEach(item => {
      const tr = document.createElement('tr');

      // ── Feature badges ──────────────────────────────────────────────
      let badges = '';
      if (item.iiif) {
        badges += `<span class="badge badge--iiif">
                     <i class="bi bi-images" aria-hidden="true"></i>IIIF
                   </span>`;
      }
      if (item.is_free_cultural_works_license) {
        badges += `<span class="badge badge--open">
                     <i class="bi bi-unlock" aria-hidden="true"></i>Open
                   </span>`;
      }
      if (!badges) {
        badges = `<span class="badge badge--standard">Standard Access</span>`;
      }

      // ── Project affiliation ─────────────────────────────────────────
      const projectHtml = item.is_part_of && item.is_part_of_project_name
        ? `<div class="library-project">
             <a href="${item.is_part_of_url}"
                target="_blank"
                rel="noopener noreferrer">
               <i class="bi bi-collection" aria-hidden="true"></i>
               ${item.is_part_of_project_name}
             </a>
           </div>`
        : '';

      // ── Visit button ────────────────────────────────────────────────
      const visitBtn = item.website
        ? `<a href="${item.website}"
              target="_blank"
              rel="noopener noreferrer"
              class="btn-visit">
             Visit
             <i class="bi bi-arrow-right-short" aria-hidden="true"></i>
           </a>`
        : `<span style="color:var(--dash-muted);font-size:.8rem">No URL</span>`;

      tr.innerHTML = `
        <td>
          <div class="library-name">${item.library}</div>
          ${projectHtml}
        </td>
        <td>
          <div class="location-nation">${item.nation}</div>
          <div class="location-city">
            <i class="bi bi-dot" aria-hidden="true"></i>${item.city}
          </div>
        </td>
        <td>${badges}</td>
        <td style="text-align:right">${visitBtn}</td>
      `;

      frag.appendChild(tr);
    });

    tableBody.appendChild(frag);
    if (showingCount) showingCount.textContent = String(data.length);
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
      const projects = new Set(
        data
          .filter(d => d.is_part_of && d.is_part_of_project_name)
          .map(d => d.is_part_of_project_name),
      );
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
      ...new Set(
        allData
          .filter(d => d.is_part_of && d.is_part_of_project_name)
          .map(d => d.is_part_of_project_name),
      ),
    ].sort();

    projects.forEach(project => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = project;
      projectSelect.appendChild(opt);
    });
  }

  // ── Filter engine ─────────────────────────────────────────────────────
  function filterData() {
    const term    = searchInput.value.toLowerCase().trim();
    const nation  = nationSelect.value;
    const project = projectSelect.value;
    const wantIIIF = iiifCheck.checked;
    const wantFree = freeCheck.checked;

    const filtered = allData.filter(d => {
      const matchSearch =
        !term ||
        d.library?.toLowerCase().includes(term) ||
        d.city?.toLowerCase().includes(term)    ||
        d.nation?.toLowerCase().includes(term)  ||
        d.is_part_of_project_name?.toLowerCase().includes(term);

      const matchNation  = nation  === 'All' || d.nation === nation;
      const matchProject = project === 'All' || d.is_part_of_project_name === project;
      const matchIIIF    = !wantIIIF || d.iiif === true;
      const matchFree    = !wantFree || d.is_free_cultural_works_license === true;

      return matchSearch && matchNation && matchProject && matchIIIF && matchFree;
    });

    renderTable(filtered);
    updateStats(filtered);
  }

  // ── Event listeners ───────────────────────────────────────────────────
  searchInput.addEventListener('input', filterData);
  nationSelect.addEventListener('change', filterData);
  projectSelect.addEventListener('change', filterData);
  iiifCheck.addEventListener('change', filterData);
  freeCheck.addEventListener('change', filterData);

  clearFiltersBtn?.addEventListener('click', () => {
    searchInput.value    = '';
    nationSelect.value   = 'All';
    projectSelect.value  = 'All';
    iiifCheck.checked    = false;
    freeCheck.checked    = false;
    filterData();
  });
});
