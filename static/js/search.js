/**
 * Search Autocomplete Module
 * Handles company search with autocomplete functionality
 */
const SearchModule = (function() {
    // Private variables
    let searchInput;
    let searchBtn;
    let dropdown;
    let debounceTimer;
    let selectedIndex = -1;
    let results = [];

    const DEBOUNCE_DELAY = 300;
    const MIN_QUERY_LENGTH = 2;

    /**
     * Initialize the search module
     */
    function init() {
        searchInput = document.getElementById('search-input');
        searchBtn = document.getElementById('search-btn');
        dropdown = document.getElementById('autocomplete-dropdown');

        if (!searchInput || !dropdown) {
            console.error('Search elements not found');
            return;
        }

        // Event listeners
        searchInput.addEventListener('input', handleInput);
        searchInput.addEventListener('keydown', handleKeydown);
        searchInput.addEventListener('focus', handleFocus);

        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                hideDropdown();
            }
        });

        searchBtn.addEventListener('click', handleSearchClick);
    }

    /**
     * Handle input changes with debouncing
     */
    function handleInput(e) {
        const query = e.target.value.trim();

        clearTimeout(debounceTimer);

        if (query.length < MIN_QUERY_LENGTH) {
            hideDropdown();
            return;
        }

        debounceTimer = setTimeout(() => fetchSuggestions(query), DEBOUNCE_DELAY);
    }

    /**
     * Handle focus event
     */
    function handleFocus() {
        const query = searchInput.value.trim();
        if (query.length >= MIN_QUERY_LENGTH && results.length > 0) {
            showDropdown();
        }
    }

    /**
     * Fetch search suggestions from API
     */
    async function fetchSuggestions(query) {
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

            if (!response.ok) {
                throw new Error('Search failed');
            }

            results = await response.json();
            renderDropdown(results);

        } catch (error) {
            console.error('Search error:', error);
            hideDropdown();
        }
    }

    /**
     * Render autocomplete dropdown
     */
    function renderDropdown(items) {
        if (items.length === 0) {
            dropdown.innerHTML = `
                <div class="autocomplete-no-results">
                    <i class="bi bi-search me-2"></i>
                    No companies found
                </div>
            `;
            showDropdown();
            return;
        }

        dropdown.innerHTML = items.map((item, index) => `
            <div class="autocomplete-item" data-ticker="${item.ticker}" data-index="${index}">
                <div class="company-name">${escapeHtml(item.name)}</div>
                <div class="ticker">${escapeHtml(item.ticker)}</div>
            </div>
        `).join('');

        // Add click handlers
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', function() {
                selectItem(this.dataset.ticker);
            });
        });

        showDropdown();
        selectedIndex = -1;
    }

    /**
     * Handle keyboard navigation
     */
    function handleKeydown(e) {
        if (dropdown.classList.contains('d-none')) {
            if (e.key === 'Enter') {
                handleSearchClick();
            }
            return;
        }

        const items = dropdown.querySelectorAll('.autocomplete-item');

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                updateSelection(items);
                break;

            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, 0);
                updateSelection(items);
                break;

            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && results[selectedIndex]) {
                    selectItem(results[selectedIndex].ticker);
                } else {
                    handleSearchClick();
                }
                break;

            case 'Escape':
                hideDropdown();
                searchInput.blur();
                break;

            case 'Tab':
                hideDropdown();
                break;
        }
    }

    /**
     * Update visual selection in dropdown
     */
    function updateSelection(items) {
        items.forEach((item, index) => {
            item.classList.toggle('active', index === selectedIndex);
        });

        // Scroll into view if needed
        if (selectedIndex >= 0 && items[selectedIndex]) {
            items[selectedIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    /**
     * Select an item and load company data
     */
    function selectItem(ticker) {
        searchInput.value = ticker;
        hideDropdown();

        // Trigger company data load
        if (typeof App !== 'undefined' && App.loadCompanyData) {
            App.loadCompanyData(ticker);
        }
    }

    /**
     * Handle search button click
     */
    function handleSearchClick() {
        const query = searchInput.value.trim();
        if (query.length >= MIN_QUERY_LENGTH) {
            hideDropdown();

            if (typeof App !== 'undefined' && App.loadCompanyData) {
                App.loadCompanyData(query.toUpperCase());
            }
        }
    }

    /**
     * Show dropdown
     */
    function showDropdown() {
        dropdown.classList.remove('d-none');
    }

    /**
     * Hide dropdown
     */
    function hideDropdown() {
        dropdown.classList.add('d-none');
        selectedIndex = -1;
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Public API
    return {
        init: init,
        hideDropdown: hideDropdown
    };
})();
