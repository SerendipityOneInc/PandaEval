// PandaEval Dashboard v4
(function () {
    // ─── Theme ───
    const themeToggle = document.getElementById('theme-toggle');
    const root = document.documentElement;

    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }

    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
    }

    // Init: use saved preference, or follow system
    const saved = localStorage.getItem('panda-theme');
    if (saved) {
        applyTheme(saved);
    } else {
        applyTheme(getSystemTheme());
    }

    // Listen for system changes (only if user hasn't manually overridden)
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
        if (!localStorage.getItem('panda-theme')) {
            applyTheme(e.matches ? 'light' : 'dark');
        }
    });

    // Toggle button
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = root.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('panda-theme', next);
        });
    }

    // ─── Dashboard ───
    const container = document.getElementById('cards-container');
    if (!container) return; // detail pages don't have cards

    const searchInput = document.getElementById('search');
    const sortSelect = document.getElementById('sort-select');
    const countEl = document.getElementById('results-count');
    const cards = () => Array.from(container.querySelectorAll('.card'));

    let filters = { domain: 'all', verdict: 'all' };

    // Stagger entrance animation
    requestAnimationFrame(() => {
        cards().forEach((c, i) => {
            c.style.animationDelay = `${Math.min(i * 0.015, 0.6)}s`;
        });
    });

    // Animate score distribution bars on load
    requestAnimationFrame(() => {
        document.querySelectorAll('.dist-bar').forEach((bar, i) => {
            const h = bar.style.height;
            bar.style.height = '0%';
            bar.style.transition = 'height 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
            bar.style.transitionDelay = `${i * 0.08}s`;
            requestAnimationFrame(() => { bar.style.height = h; });
        });
    });

    // Filter buttons (pills + domain pills)
    document.querySelectorAll('.pill[data-group], .domain-pill[data-group]').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.dataset.group;
            const value = btn.dataset.filter;
            filters[group] = value;
            const selector = group === 'domain' ? '.domain-pill[data-group="domain"]' : '.pill[data-group="verdict"]';
            document.querySelectorAll(selector).forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyFilters();
        });
    });

    // Search
    let debounce;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(applyFilters, 80);
    });

    // Sort
    sortSelect.addEventListener('change', () => { sortCards(); applyFilters(); });

    // View toggle
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            container.classList.toggle('list-view', btn.dataset.view === 'list');
        });
    });

    function applyFilters() {
        const q = searchInput.value.toLowerCase().trim();
        let shown = 0;
        const all = cards();

        all.forEach(card => {
            const name = card.dataset.name || '';
            const domain = card.dataset.domain || '';
            const verdict = card.dataset.verdict || '';
            const text = card.textContent.toLowerCase();

            let ok = true;
            if (filters.domain !== 'all' && domain !== filters.domain) ok = false;
            if (filters.verdict !== 'all' && verdict !== filters.verdict) ok = false;
            if (q && !text.includes(q)) ok = false;

            card.classList.toggle('hidden', !ok);
            if (ok) shown++;
        });

        if (countEl) {
            countEl.textContent = (q || filters.domain !== 'all' || filters.verdict !== 'all')
                ? `${shown}/${all.length}` : '';
        }
    }

    function sortCards() {
        const v = sortSelect.value;
        const all = cards();
        all.sort((a, b) => {
            switch (v) {
                case 'score-desc': return parseFloat(b.dataset.score) - parseFloat(a.dataset.score);
                case 'score-asc': return parseFloat(a.dataset.score) - parseFloat(b.dataset.score);
                case 'name-asc': return a.dataset.name.localeCompare(b.dataset.name);
                case 'name-desc': return b.dataset.name.localeCompare(a.dataset.name);
                case 'downloads-desc': return parseInt(b.dataset.downloads) - parseInt(a.dataset.downloads);
                default: return 0;
            }
        });
        all.forEach(c => container.appendChild(c));
    }

    // Keyboard: / to focus search, Esc to clear
    document.addEventListener('keydown', e => {
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
