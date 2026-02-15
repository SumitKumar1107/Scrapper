/**
 * Main Application Module
 * Orchestrates the financial data scraper application
 */
const App = (function() {
    // Private variables
    let currentData = null;
    let currentTicker = null;
    let currentPeriod = 'quarterly';

    // DOM elements
    let loadingSpinner;
    let errorAlert;
    let errorMessage;
    let companyInfo;
    let dataToggle;
    let chartsSection;
    let refreshBtn;
    let cacheTime;

    /**
     * Initialize the application
     */
    function init() {
        // Cache DOM elements
        loadingSpinner = document.getElementById('loading-spinner');
        errorAlert = document.getElementById('error-alert');
        errorMessage = document.getElementById('error-message');
        companyInfo = document.getElementById('company-info');
        dataToggle = document.getElementById('data-toggle');
        chartsSection = document.getElementById('charts-section');
        refreshBtn = document.getElementById('refresh-btn');
        cacheTime = document.getElementById('cache-time');

        // Period toggle handlers
        document.querySelectorAll('input[name="period"]').forEach(radio => {
            radio.addEventListener('change', function(e) {
                currentPeriod = e.target.value;
                if (currentData) {
                    updateCharts();
                }
            });
        });

        // Refresh button handler
        if (refreshBtn) {
            refreshBtn.addEventListener('click', handleRefresh);
        }

        // Check URL for initial company
        checkUrlParams();
    }

    /**
     * Check URL parameters for initial company
     */
    function checkUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const ticker = params.get('ticker');
        if (ticker) {
            document.getElementById('search-input').value = ticker;
            loadCompanyData(ticker);
        }
    }

    /**
     * Load company data from API
     */
    async function loadCompanyData(ticker, forceRefresh = false) {
        if (!ticker) return;

        ticker = ticker.toUpperCase().trim();
        currentTicker = ticker;

        showLoading();
        hideError();
        hideDataSections();

        // Update URL
        updateUrl(ticker);

        try {
            let url = `/api/company/${encodeURIComponent(ticker)}`;
            if (forceRefresh) {
                url += '?refresh=true';
            }

            const response = await fetch(url);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to fetch company data');
            }

            currentData = await response.json();

            renderCompanyInfo(currentData.company_info);
            updateCharts();
            updateCacheInfo(currentData);
            showDataSections();

        } catch (error) {
            console.error('Load error:', error);
            showError(error.message);
        } finally {
            hideLoading();
        }
    }

    /**
     * Handle refresh button click
     */
    async function handleRefresh() {
        if (!currentTicker) return;

        refreshBtn.classList.add('spinning');
        refreshBtn.disabled = true;

        try {
            await loadCompanyData(currentTicker, true);
        } finally {
            refreshBtn.classList.remove('spinning');
            refreshBtn.disabled = false;
        }
    }

    /**
     * Render company information
     */
    function renderCompanyInfo(info) {
        // Company name and ticker
        document.getElementById('company-name').textContent = info.name || '';
        document.getElementById('company-ticker').textContent = info.ticker || '';
        document.getElementById('bse-code').textContent = info.bse_code || '-';
        document.getElementById('nse-code').textContent = info.nse_code || info.ticker || '-';

        // Current price
        const priceEl = document.getElementById('current-price');
        if (info.current_price != null) {
            priceEl.innerHTML = `&#8377; ${formatNumber(info.current_price)}`;
        } else {
            priceEl.textContent = '-';
        }

        // Price change
        const changeEl = document.getElementById('price-change');
        if (info.price_change_percent != null) {
            const isPositive = info.price_change_percent >= 0;
            const sign = isPositive ? '+' : '';
            changeEl.textContent = `${sign}${info.price_change_percent.toFixed(2)}%`;
            changeEl.className = `badge fs-6 ${isPositive ? 'price-positive' : 'price-negative'}`;
        } else {
            changeEl.textContent = '';
            changeEl.className = 'badge fs-6';
        }

        // Key ratios - format market cap to always show " Cr" at end
        let marketCap = info.market_cap || '-';
        if (marketCap && marketCap !== '-') {
            // Remove any existing Cr/Cr./CR at end, then add " Cr"
            marketCap = marketCap.replace(/\s*[Cc][Rr]\.?\s*$/, '') + ' Cr';
        }
        document.getElementById('market-cap').textContent = marketCap;
        document.getElementById('pe-ratio').textContent =
            info.pe_ratio != null ? info.pe_ratio.toFixed(2) : '-';
        document.getElementById('pb-ratio').textContent =
            info.pb_ratio != null ? info.pb_ratio.toFixed(2) : '-';
        document.getElementById('roce').textContent =
            info.roce != null ? `${info.roce}%` : '-';
        document.getElementById('roe').textContent =
            info.roe != null ? `${info.roe}%` : '-';
        document.getElementById('debt').textContent = info.debt || '-';
        document.getElementById('debt-to-equity').textContent =
            info.debt_to_equity != null ? info.debt_to_equity.toFixed(2) : '-';
    }

    /**
     * Update charts based on current period
     */
    function updateCharts() {
        const data = currentPeriod === 'quarterly'
            ? currentData.quarterly_data
            : currentData.annual_data;

        // Always use annual data for cash flow (not available in quarterly)
        ChartsModule.renderAllCharts(data, currentData.annual_data);

        // Shareholding chart (independent of main period toggle)
        updateShareholdingChart();
    }

    /**
     * Update shareholding chart based on its own toggles
     */
    function updateShareholdingChart() {
        const shData = currentPeriod === 'quarterly'
            ? currentData.shareholding_quarterly
            : currentData.shareholding_yearly;

        const companyName = currentData.company_info ? currentData.company_info.name : '';
        const titleEl = document.getElementById('shareholding-title');
        if (titleEl) {
            titleEl.textContent = `Shareholding Pattern - ${companyName || ''}`.trim();
        }

        ChartsModule.renderShareholdingChart(shData, companyName);
    }

    /**
     * Update cache info display
     */
    function updateCacheInfo(data) {
        if (data.cached_at) {
            const cachedDate = new Date(data.cached_at);
            const timeStr = cachedDate.toLocaleString('en-IN', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
            cacheTime.textContent = `Last updated: ${timeStr}`;
        } else {
            cacheTime.textContent = 'Fresh data';
        }
    }

    /**
     * Update URL with ticker parameter
     */
    function updateUrl(ticker) {
        const url = new URL(window.location);
        url.searchParams.set('ticker', ticker);
        window.history.replaceState({}, '', url);
    }

    /**
     * Show loading spinner
     */
    function showLoading() {
        if (loadingSpinner) {
            loadingSpinner.classList.remove('d-none');
        }
    }

    /**
     * Hide loading spinner
     */
    function hideLoading() {
        if (loadingSpinner) {
            loadingSpinner.classList.add('d-none');
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        if (errorAlert && errorMessage) {
            errorMessage.textContent = message;
            errorAlert.classList.remove('d-none');
        }
    }

    /**
     * Hide error message
     */
    function hideError() {
        if (errorAlert) {
            errorAlert.classList.add('d-none');
        }
    }

    /**
     * Show data sections
     */
    function showDataSections() {
        if (companyInfo) companyInfo.classList.remove('d-none');
        if (dataToggle) dataToggle.classList.remove('d-none');
        if (chartsSection) chartsSection.classList.remove('d-none');
    }

    /**
     * Hide data sections
     */
    function hideDataSections() {
        if (companyInfo) companyInfo.classList.add('d-none');
        if (dataToggle) dataToggle.classList.add('d-none');
        if (chartsSection) chartsSection.classList.add('d-none');
    }

    /**
     * Format number with Indian numbering system
     */
    function formatNumber(num) {
        if (num == null) return '-';
        return num.toLocaleString('en-IN', { maximumFractionDigits: 2 });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Public API
    return {
        loadCompanyData: loadCompanyData,
        getCurrentData: function() { return currentData; },
        getCurrentTicker: function() { return currentTicker; }
    };
})();
