// PandaEval Dashboard — Enhanced interactions
(function () {
    const container = document.getElementById('cards-container');
    const searchInput = document.getElementById('search');
    const sortSelect = document.getElementById('sort-select');
    const resultsCount = document.getElementById('results-count');
    const cards = () => Array.from(container.querySelectorAll('.card'));

    let activeFilters = { domain: 'all', verdict: 'all' };

    // Stagger card reveal animations
    function staggerCards() {
        const visible = cards().filter(c => !c.classList.contains('hidden'));
        visible.forEach((card, i) => {
            card.style.animationDelay = `${Math.min(i * 0.03, 0.6)}s`;
            card.classList.remove('card-reveal');
            void card.offsetWidth; // trigger reflow
            card.classList.add('card-reveal');
        });
    }

    // Initial stagger
    requestAnimationFrame(() => {
        cards().forEach((card, i) => {
            card.style.animationDelay = `${Math.min(i * 0.025, 1.2)}s`;
        });
    });

    // Filter buttons (both toolbar and domain row)
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.dataset.group;
            const value = btn.dataset.filter;
            activeFilters[group] = value;
            // Update active state for all buttons in both toolbar and domain row
            document.querySelectorAll(`.filter-btn[data-group="${group}"]`).forEach(b => b.classList.remove('active'));
            // Activate all buttons matching this filter value in this group
            document.querySelectorAll(`.filter-btn[data-group="${group}"][data-filter="${value}"]`).forEach(b => b.classList.add('active'));
            applyFilters();
        });
    });

    // Search with debounce
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => applyFilters(), 120);
    });

    // Sort
    sortSelect.addEventListener('change', () => {
        sortCards();
        applyFilters();
    });

    // View toggle
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (btn.dataset.view === 'list') {
                container.classList.add('list-view');
            } else {
                container.classList.remove('list-view');
            }
        });
    });

    function applyFilters() {
        const query = searchInput.value.toLowerCase().trim();
        let visibleCount = 0;

        cards().forEach(card => {
            const name = card.dataset.name || '';
            const domain = card.dataset.domain || '';
            const verdict = card.dataset.verdict || '';
            const text = card.textContent.toLowerCase();

            let show = true;
            if (activeFilters.domain !== 'all' && domain !== activeFilters.domain) show = false;
            if (activeFilters.verdict !== 'all' && verdict !== activeFilters.verdict) show = false;
            if (query && !text.includes(query)) show = false;

            card.classList.toggle('hidden', !show);
            if (show) visibleCount++;
        });

        // Update count
        if (resultsCount) {
            const total = cards().length;
            if (query || activeFilters.domain !== 'all' || activeFilters.verdict !== 'all') {
                resultsCount.textContent = `${visibleCount}/${total}`;
            } else {
                resultsCount.textContent = '';
            }
        }

        staggerCards();
    }

    function sortCards() {
        const val = sortSelect.value;
        const allCards = cards();
        allCards.sort((a, b) => {
            switch (val) {
                case 'score-desc': return parseFloat(b.dataset.score) - parseFloat(a.dataset.score);
                case 'score-asc': return parseFloat(a.dataset.score) - parseFloat(b.dataset.score);
                case 'name-asc': return a.dataset.name.localeCompare(b.dataset.name);
                case 'name-desc': return b.dataset.name.localeCompare(a.dataset.name);
                case 'downloads-desc': return parseInt(b.dataset.downloads) - parseInt(a.dataset.downloads);
                default: return 0;
            }
        });
        allCards.forEach(c => container.appendChild(c));
    }

    // Keyboard shortcut: focus search with /
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
        if (e.key === 'Escape' && document.activeElement === searchInput) {
            searchInput.value = '';
            searchInput.blur();
            applyFilters();
        }
    });
})();
