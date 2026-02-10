// Theme Toggle - Matches MkDocs Material behavior
(function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Set initial theme: saved preference > system preference > light
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', initialTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    let allData = [];
    let sortColumn = null;
    let sortDirection = 'asc';
    const loader = document.getElementById('loader');

    // UI Elements
    const tableBody = document.getElementById('tableBody');
    const emptyState = document.getElementById('emptyState');
    const searchInput = document.getElementById('searchInput');
    const nationSelect = document.getElementById('nationSelect');
    const projectSelect = document.getElementById('projectSelect');
    const iiifCheck = document.getElementById('iiifCheck');
    const freeCheck = document.getElementById('freeCheck');
    const clearFiltersBtn = document.getElementById('clearFilters');

    // Stats Elements
    const statTotal = document.getElementById('statTotal');
    const statNations = document.getElementById('statNations');
    const statIIIF = document.getElementById('statIIIF');
    const statProjects = document.getElementById('statProjects');
    const showingCount = document.getElementById('showingCount');

    // 1. Fetch Data
    fetch('data.json')
        .then(response => {
            if (!response.ok) throw new Error("Failed to load data");
            return response.json();
        })
        .then(data => {
            // Sort alphabetically by Library Name initially
            allData = data.sort((a, b) => a.library.localeCompare(b.library));

            initializeDashboard();
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 500); // Smooth fade out
        })
        .catch(err => {
            loader.innerHTML = `<div class="text-danger text-center"><i class="bi bi-exclamation-triangle fs-1"></i><p class="mt-2">Error loading data.json<br><small>${err.message}</small></p></div>`;
        });

    function initializeDashboard() {
        populateNationFilter();
        populateProjectFilter();
        updateStats(allData);
        renderTable(allData);
        initializeSorting();
    }

    // Sorting functionality
    function initializeSorting() {
        const sortableHeaders = document.querySelectorAll('.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');
                handleSort(column, header);
            });
        });
    }

    function handleSort(column, headerElement) {
        // Toggle sort direction if clicking the same column
        if (sortColumn === column) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            sortColumn = column;
            sortDirection = 'asc';
        }

        // Update all header states
        document.querySelectorAll('.sortable').forEach(header => {
            header.classList.remove('active');
            header.removeAttribute('data-sort-direction');
        });

        // Mark active header
        headerElement.classList.add('active');
        headerElement.setAttribute('data-sort-direction', sortDirection);

        // Sort the data
        sortData();

        // Re-apply filters and render
        filterData();
    }

    function sortData() {
        allData.sort((a, b) => {
            let valA = a[sortColumn];
            let valB = b[sortColumn];

            // Handle null/undefined values
            if (valA == null) valA = '';
            if (valB == null) valB = '';

            // Convert to lowercase for case-insensitive sorting
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();

            // Compare values
            if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }

    // 2. Render Table
    function renderTable(data) {
        tableBody.innerHTML = '';

        if (data.length === 0) {
            tableBody.parentElement.classList.add('d-none'); // Hide table
            emptyState.classList.remove('d-none');
            showingCount.innerText = 0;
            return;
        }

        tableBody.parentElement.classList.remove('d-none');
        emptyState.classList.add('d-none');

        const fragment = document.createDocumentFragment();

        data.forEach(item => {
            const row = document.createElement('tr');

            // Logic for Badges
            let badges = '';
            if (item.iiif === true) {
                badges += `<span class="badge badge-feature bg-iiif me-1" title="International Image Interoperability Framework"><i class="bi bi-images me-1"></i>IIIF</span>`;
            }
            if (item.is_free_cultural_works_license === true) {
                badges += `<span class="badge badge-feature bg-free" title="Free Cultural Works License"><i class="bi bi-unlock me-1"></i>Open</span>`;
            }
            if (!badges) {
                badges = `<span class="text-muted small fst-italic">Standard Access</span>`;
            }

            // Project affiliation badge
            const projectBadge = item.is_part_of && item.is_part_of_project_name
                ? `<div class="small mt-1"><a href="${item.is_part_of_url}" target="_blank" class="text-muted text-decoration-none"><i class="bi bi-collection me-1"></i>${item.is_part_of_project_name}</a></div>`
                : '';

            // Website handling
            const websiteBtn = item.website
                ? `<a href="${item.website}" target="_blank" class="btn btn-sm btn-outline-primary rounded-pill">Visit <i class="bi bi-arrow-right-short"></i></a>`
                : `<span class="text-muted small">No URL</span>`;

            row.innerHTML = `
                <td>
                    <div class="library-name">${item.library}</div>
                    ${projectBadge}
                </td>
                <td>
                    <div class="fw-medium">${item.nation}</div>
                    <div class="city-name"><i class="bi bi-dot"></i> ${item.city}</div>
                </td>
                <td>${badges}</td>
                <td class="text-end">${websiteBtn}</td>
            `;
            fragment.appendChild(row);
        });

        tableBody.appendChild(fragment);
        showingCount.innerText = data.length; // Approximate visible count
    }

    // 3. Stats Logic
    function updateStats(data) {
        // Calculate Total Active Libraries
        statTotal.innerText = data.length;

        // Calculate Unique Nations
        const uniqueNations = new Set(data.map(item => item.nation));
        statNations.innerText = uniqueNations.size;

        // Calculate IIIF Count
        statIIIF.innerText = data.filter(item => item.iiif === true).length;

        // Calculate Active Projects Count
        const uniqueProjects = new Set(
            data
                .filter(item => item.is_part_of === true && item.is_part_of_project_name)
                .map(item => item.is_part_of_project_name)
        );
        statProjects.innerText = uniqueProjects.size;
    }

    // 4. Populate Dropdown
    function populateNationFilter() {
        // Extract unique nations, sort them
        const nations = [...new Set(allData.map(item => item.nation))].sort();

        nations.forEach(nation => {
            const option = document.createElement('option');
            option.value = nation;
            option.textContent = nation;
            nationSelect.appendChild(option);
        });
    }

    function populateProjectFilter() {
        // Extract unique project names from items where is_part_of is true, sort them
        const projects = [...new Set(
            allData
                .filter(item => item.is_part_of === true && item.is_part_of_project_name)
                .map(item => item.is_part_of_project_name)
        )].sort();

        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project;
            option.textContent = project;
            projectSelect.appendChild(option);
        });
    }

    // 5. Filter Engine
    function filterData() {
        const term = searchInput.value.toLowerCase().trim();
        const selectedNation = nationSelect.value;
        const selectedProject = projectSelect.value;
        const requireIIIF = iiifCheck.checked;
        const requireFree = freeCheck.checked;

        const filtered = allData.filter(item => {
            // Search Text - include nation in search, handle empty search
            const matchesSearch = !term ||
                (item.library && item.library.toLowerCase().includes(term)) ||
                (item.city && item.city.toLowerCase().includes(term)) ||
                (item.nation && item.nation.toLowerCase().includes(term)) ||
                (item.is_part_of_project_name && item.is_part_of_project_name.toLowerCase().includes(term));

            // Nation Filter
            const matchesNation = selectedNation === 'All' || item.nation === selectedNation;

            // Project Filter
            const matchesProject = selectedProject === 'All' || item.is_part_of_project_name === selectedProject;

            // Checkbox Filters
            const matchesIIIF = !requireIIIF || item.iiif === true;
            const matchesFree = !requireFree || item.is_free_cultural_works_license === true;

            return matchesSearch && matchesNation && matchesProject && matchesIIIF && matchesFree;
        });

        renderTable(filtered);
        updateStats(filtered); // Update stats with filtered data
    }

    // Event Listeners
    searchInput.addEventListener('input', filterData);
    nationSelect.addEventListener('change', filterData);
    projectSelect.addEventListener('change', filterData);
    iiifCheck.addEventListener('change', filterData);
    freeCheck.addEventListener('change', filterData);

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            searchInput.value = '';
            nationSelect.value = 'All';
            projectSelect.value = 'All';
            iiifCheck.checked = false;
            freeCheck.checked = false;
            filterData();
        });
    }
});