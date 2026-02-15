/**
 * AI Research Module
 * Handles AI-generated company research analysis
 */
const ResearchModule = (function() {
    let section;
    let generateBtn;
    let regenerateBtn;
    let loadingEl;
    let errorEl;
    let errorMessageEl;
    let contentEl;
    let bodyEl;
    let generatedAtEl;
    let placeholderEl;

    function init() {
        section = document.getElementById('ai-research-section');
        generateBtn = document.getElementById('generate-research-btn');
        regenerateBtn = document.getElementById('regenerate-research-btn');
        loadingEl = document.getElementById('research-loading');
        errorEl = document.getElementById('research-error');
        errorMessageEl = document.getElementById('research-error-message');
        contentEl = document.getElementById('research-content');
        bodyEl = document.getElementById('research-body');
        generatedAtEl = document.getElementById('research-generated-at');
        placeholderEl = document.getElementById('research-placeholder');

        if (generateBtn) {
            generateBtn.addEventListener('click', function() {
                handleGenerate(false);
            });
        }

        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', function() {
                handleGenerate(true);
            });
        }
    }

    function show() {
        if (section) {
            section.classList.remove('d-none');
            resetState();
        }
    }

    function hide() {
        if (section) {
            section.classList.add('d-none');
            resetState();
        }
    }

    function resetState() {
        if (loadingEl) loadingEl.classList.add('d-none');
        if (errorEl) errorEl.classList.add('d-none');
        if (contentEl) contentEl.classList.add('d-none');
        if (placeholderEl) placeholderEl.classList.remove('d-none');
        if (generateBtn) {
            generateBtn.classList.remove('d-none');
            generateBtn.disabled = false;
        }
        if (regenerateBtn) regenerateBtn.classList.add('d-none');
    }

    async function handleGenerate(forceRefresh) {
        let ticker = null;
        let companyName = null;

        if (typeof App !== 'undefined') {
            ticker = App.getCurrentTicker();
            const data = App.getCurrentData();
            if (data && data.company_info) {
                companyName = data.company_info.name;
            }
        }

        if (!ticker || !companyName) {
            showError('No company selected. Please search for a company first.');
            return;
        }

        showLoading();

        try {
            let url = `/api/research/${encodeURIComponent(ticker)}?company_name=${encodeURIComponent(companyName)}`;
            if (forceRefresh) {
                url += '&refresh=true';
            }

            const response = await fetch(url);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate research');
            }

            const result = await response.json();
            showContent(result);

        } catch (error) {
            console.error('Research error:', error);
            showError(error.message);
        }
    }

    function showLoading() {
        if (placeholderEl) placeholderEl.classList.add('d-none');
        if (contentEl) contentEl.classList.add('d-none');
        if (errorEl) errorEl.classList.add('d-none');
        if (loadingEl) loadingEl.classList.remove('d-none');
        if (generateBtn) generateBtn.disabled = true;
        if (regenerateBtn) regenerateBtn.classList.add('d-none');
    }

    function showContent(result) {
        if (loadingEl) loadingEl.classList.add('d-none');
        if (placeholderEl) placeholderEl.classList.add('d-none');
        if (errorEl) errorEl.classList.add('d-none');

        if (bodyEl && result.analysis) {
            if (typeof marked !== 'undefined') {
                bodyEl.innerHTML = marked.parse(result.analysis);
            } else {
                bodyEl.textContent = result.analysis;
                bodyEl.style.whiteSpace = 'pre-wrap';
            }
        }

        if (generatedAtEl && result.generated_at) {
            const date = new Date(result.generated_at);
            generatedAtEl.textContent = date.toLocaleString('en-IN', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        if (contentEl) contentEl.classList.remove('d-none');
        if (generateBtn) generateBtn.classList.add('d-none');
        if (regenerateBtn) {
            regenerateBtn.classList.remove('d-none');
            regenerateBtn.disabled = false;
        }
    }

    function showError(message) {
        if (loadingEl) loadingEl.classList.add('d-none');
        if (placeholderEl) placeholderEl.classList.add('d-none');
        if (contentEl) contentEl.classList.add('d-none');
        if (errorMessageEl) errorMessageEl.textContent = message;
        if (errorEl) errorEl.classList.remove('d-none');
        if (generateBtn) {
            generateBtn.classList.remove('d-none');
            generateBtn.disabled = false;
        }
        if (regenerateBtn) regenerateBtn.classList.add('d-none');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return {
        show: show,
        hide: hide,
        resetState: resetState
    };
})();
