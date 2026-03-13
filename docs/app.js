// PandaEval Dashboard — filtering, sorting, search, view toggle
(function () {
    const container = document.getElementById('cards-container');
    const searchInput = document.getElementById('search');
    const sortSelect = document.getElementById('sort-select');
    const cards = () => Array.from(container.querySelectorAll('.card'));

    let activeFilters = { domain: 'all', verdict: 'all' };

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.dataset.group;
            const value = btn.dataset.filter;
            activeFilters[group] = value;
            // Update active state
            document.querySelectorAll(`.filter-btn[data-group="${group}"]`).forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyFilters();
        });
    });

    // Search
    searchInput.addEventListener('input', () => applyFilters());

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
        });
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
})();
