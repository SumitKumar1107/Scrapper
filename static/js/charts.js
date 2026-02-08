/**
 * Charts Module
 * Handles Plotly chart rendering for financial data
 */
const ChartsModule = (function() {
    // Chart configuration - only show download PNG button
    const chartConfig = {
        responsive: true,
        displayModeBar: true,
        modeBarButtons: [['toImage']],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: 'financial_chart',
            height: 700,
            width: 1400,
            scale: 2
        }
    };

    // Base layout configuration
    const baseLayout = {
        margin: { t: 50, r: 60, b: 120, l: 100 },
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2,
            x: 0.5,
            xanchor: 'center',
            font: { color: '#333333' }
        },
        hovermode: 'x unified',
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#ffffff',
        font: {
            family: 'system-ui, -apple-system, sans-serif',
            size: 12,
            color: '#333333'
        },
        xaxis: {
            showgrid: false,
            showline: true,
            linecolor: '#dee2e6',
            automargin: true,
            tickfont: { size: 11, color: '#333333' },
            title: { font: { color: '#333333' } }
        },
        yaxis: {
            showgrid: true,
            gridcolor: '#f0f0f0',
            showline: true,
            linecolor: '#dee2e6',
            zeroline: true,
            zerolinecolor: '#dee2e6',
            automargin: true,
            tickfont: { color: '#333333' },
            title: { font: { color: '#333333' } }
        },
        bargap: 0.3,
        bargroupgap: 0.1
    };

    // Color palette
    const colors = {
        primary: '#0d6efd',
        success: '#198754',
        info: '#0dcaf0',
        warning: '#fd7e14',
        purple: '#6f42c1',
        danger: '#dc3545'
    };

    // Calculate chart width based on number of data points
    function calculateChartWidth(numPeriods, minWidthPerBar = 50, minWidth = 400, maxWidth = null) {
        const calculatedWidth = Math.max(minWidth, numPeriods * minWidthPerBar + 150);
        if (maxWidth) {
            return Math.min(calculatedWidth, maxWidth);
        }
        return calculatedWidth;
    }

    // Set container width and render chart
    function setContainerWidth(containerId, numPeriods) {
        const container = document.getElementById(containerId);
        if (container) {
            const width = calculateChartWidth(numPeriods);
            const parentWidth = container.parentElement.offsetWidth;
            // Only constrain if calculated width is less than parent
            if (width < parentWidth) {
                container.style.width = width + 'px';
            } else {
                container.style.width = '100%';
            }
        }
    }

    /**
     * Render Sales/Revenue bar chart
     */
    function renderSalesChart(data, containerId = 'sales-chart') {
        if (!data.periods || data.periods.length === 0) {
            showNoData(containerId);
            return;
        }

        // Set container width based on data
        setContainerWidth(containerId, data.periods.length);

        const trace = {
            x: data.periods,
            y: data.sales,
            type: 'bar',
            name: 'Sales',
            marker: {
                color: colors.primary,
                line: {
                    color: colors.primary,
                    width: 1
                }
            },
            hovertemplate: '<b>%{x}</b><br>Sales: %{y:,.0f} Cr<extra></extra>'
        };

        const layout = {
            ...baseLayout,
            yaxis: {
                ...baseLayout.yaxis,
                title: { text: 'Amount (Cr)', standoff: 10 },
                tickformat: ',.0f'
            },
            xaxis: {
                ...baseLayout.xaxis,
                tickangle: -45,
                range: [-0.5, data.periods.length - 0.5],
                dtick: 1
            }
        };

        Plotly.newPlot(containerId, [trace], layout, chartConfig);
    }

    /**
     * Render Operating Profit and Net Profit comparison chart
     */
    function renderProfitChart(data, containerId = 'profit-chart') {
        if (!data.periods || data.periods.length === 0) {
            showNoData(containerId);
            return;
        }

        // Set container width based on data
        setContainerWidth(containerId, data.periods.length);

        const operatingTrace = {
            x: data.periods,
            y: data.operating_profit,
            type: 'bar',
            name: 'Operating Profit',
            marker: { color: colors.success },
            hovertemplate: '<b>%{x}</b><br>Operating Profit: %{y:,.0f} Cr<extra></extra>'
        };

        const netTrace = {
            x: data.periods,
            y: data.net_profit,
            type: 'bar',
            name: 'Net Profit',
            marker: { color: colors.info },
            hovertemplate: '<b>%{x}</b><br>Net Profit: %{y:,.0f} Cr<extra></extra>'
        };

        const layout = {
            ...baseLayout,
            barmode: 'group',
            yaxis: {
                ...baseLayout.yaxis,
                title: { text: 'Amount (Cr)', standoff: 10 },
                tickformat: ',.0f'
            },
            xaxis: {
                ...baseLayout.xaxis,
                tickangle: -45,
                range: [-0.5, data.periods.length - 0.5],
                dtick: 1
            }
        };

        Plotly.newPlot(containerId, [operatingTrace, netTrace], layout, chartConfig);
    }

    /**
     * Render Profit Margins line chart
     */
    function renderMarginsChart(data, containerId = 'margins-chart') {
        if (!data.periods || data.periods.length === 0) {
            showNoData(containerId);
            return;
        }

        // Set container width based on data
        setContainerWidth(containerId, data.periods.length);

        const traces = [];

        // Calculate Gross Margin % = (Sales - Material Cost) / Sales * 100
        const grossMarginPercent = data.periods.map((_, i) => {
            if (data.sales[i] && data.material_cost && data.material_cost[i] != null && data.sales[i] !== 0) {
                return ((data.sales[i] - data.material_cost[i]) / data.sales[i]) * 100;
            }
            return null;
        });

        // Only add Gross Margin trace if we have valid data
        const hasGrossMargin = grossMarginPercent.some(v => v !== null);
        if (hasGrossMargin) {
            traces.push({
                x: data.periods,
                y: grossMarginPercent,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Gross Margin %',
                line: { color: colors.primary, width: 2 },
                marker: { size: 8 },
                hovertemplate: '<b>%{x}</b><br>Gross Margin: %{y:.1f}%<extra></extra>'
            });
        }

        // Operating Profit Margin
        traces.push({
            x: data.periods,
            y: data.opm_percent,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'OPM %',
            line: { color: colors.success, width: 2 },
            marker: { size: 8 },
            hovertemplate: '<b>%{x}</b><br>OPM: %{y:.1f}%<extra></extra>'
        });

        // Calculate Net Profit Margin
        const npmPercent = data.periods.map((_, i) => {
            if (data.sales[i] && data.net_profit[i] && data.sales[i] !== 0) {
                return ((data.net_profit[i] / data.sales[i]) * 100);
            }
            return null;
        });

        traces.push({
            x: data.periods,
            y: npmPercent,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'NPM %',
            line: { color: colors.purple, width: 2 },
            marker: { size: 8 },
            hovertemplate: '<b>%{x}</b><br>NPM: %{y:.1f}%<extra></extra>'
        });

        const layout = {
            ...baseLayout,
            yaxis: {
                ...baseLayout.yaxis,
                title: { text: 'Margin (%)', standoff: 10 },
                tickformat: '.1f',
                ticksuffix: '%'
            },
            xaxis: {
                ...baseLayout.xaxis,
                tickangle: -45,
                range: [-0.5, data.periods.length - 0.5]
            }
        };

        Plotly.newPlot(containerId, traces, layout, chartConfig);
    }

    /**
     * Render EPS line chart with area fill
     */
    function renderEPSChart(data, containerId = 'eps-chart') {
        if (!data.periods || data.periods.length === 0) {
            showNoData(containerId);
            return;
        }

        // Set container width based on data
        setContainerWidth(containerId, data.periods.length);

        const trace = {
            x: data.periods,
            y: data.eps,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'EPS',
            line: { color: colors.warning, width: 3 },
            marker: { size: 10, color: colors.warning },
            fill: 'tozeroy',
            fillcolor: 'rgba(253, 126, 20, 0.1)',
            hovertemplate: '<b>%{x}</b><br>EPS: Rs %{y:.2f}<extra></extra>'
        };

        const layout = {
            ...baseLayout,
            yaxis: {
                ...baseLayout.yaxis,
                title: { text: 'EPS (Rs)', standoff: 10 },
                tickformat: '.2f',
                tickprefix: 'Rs '
            },
            xaxis: {
                ...baseLayout.xaxis,
                tickangle: -45,
                range: [-0.5, data.periods.length - 0.5]
            }
        };

        Plotly.newPlot(containerId, [trace], layout, chartConfig);
    }

    /**
     * Show no data message in chart container
     */
    function showNoData(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="d-flex align-items-center justify-content-center h-100 text-muted">
                    <div class="text-center">
                        <i class="bi bi-bar-chart fs-1 mb-2 d-block"></i>
                        <p class="mb-0">No data available</p>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Render Sales Breakdown stacked bar chart
     * Shows how expenses, interest, depreciation, tax eat into sales
     */
    function renderSalesBreakdownChart(data, containerId = 'breakdown-chart') {
        if (!data.periods || data.periods.length === 0) {
            showNoData(containerId);
            return;
        }

        // Set container width based on data
        setContainerWidth(containerId, data.periods.length);

        // Calculate tax amount (PBT - Net Profit)
        const taxAmount = data.periods.map((_, i) => {
            if (data.profit_before_tax[i] != null && data.net_profit[i] != null) {
                return Math.max(0, data.profit_before_tax[i] - data.net_profit[i]);
            }
            return 0;
        });

        // Calculate other expenses (Sales - Material Cost - Operating Profit - Other Income)
        // Or simply: Expenses - Material Cost (if expenses includes everything)
        const otherExpenses = data.periods.map((_, i) => {
            if (data.expenses[i] != null) {
                // Expenses typically includes material cost
                const matCost = data.material_cost[i] || 0;
                return Math.max(0, data.expenses[i] - matCost);
            }
            return 0;
        });

        const traces = [];

        // Material Cost / COGS
        if (data.material_cost && data.material_cost.some(v => v != null && v > 0)) {
            traces.push({
                x: data.periods,
                y: data.material_cost,
                type: 'bar',
                name: 'Material Cost',
                marker: { color: '#6c757d' },
                hovertemplate: data.periods.map((period, i) => {
                    const pct = data.sales[i] ? ((data.material_cost[i] || 0) / data.sales[i] * 100).toFixed(1) : 0;
                    return `Material Cost: %{y:,.0f} Cr (<b>${pct}%</b>)<extra></extra>`;
                })
            });
        }

        // Other Operating Expenses
        if (otherExpenses.some(v => v > 0)) {
            traces.push({
                x: data.periods,
                y: otherExpenses,
                type: 'bar',
                name: 'Operating Expenses',
                marker: { color: '#fd7e14' },
                hovertemplate: data.periods.map((period, i) => {
                    const pct = data.sales[i] ? (otherExpenses[i] / data.sales[i] * 100).toFixed(1) : 0;
                    return `Operating Expenses: ${otherExpenses[i].toFixed(0)} Cr (<b>${pct}%</b>)<extra></extra>`;
                })
            });
        }

        // Depreciation
        if (data.depreciation && data.depreciation.some(v => v != null && v > 0)) {
            traces.push({
                x: data.periods,
                y: data.depreciation,
                type: 'bar',
                name: 'Depreciation',
                marker: { color: '#6f42c1' },
                hovertemplate: data.periods.map((period, i) => {
                    const pct = data.sales[i] ? ((data.depreciation[i] || 0) / data.sales[i] * 100).toFixed(1) : 0;
                    return `Depreciation: %{y:,.0f} Cr (<b>${pct}%</b>)<extra></extra>`;
                })
            });
        }

        // Interest
        if (data.interest && data.interest.some(v => v != null && v > 0)) {
            traces.push({
                x: data.periods,
                y: data.interest,
                type: 'bar',
                name: 'Interest',
                marker: { color: '#dc3545' },
                hovertemplate: data.periods.map((period, i) => {
                    const pct = data.sales[i] ? ((data.interest[i] || 0) / data.sales[i] * 100).toFixed(1) : 0;
                    return `Interest: %{y:,.0f} Cr (<b>${pct}%</b>)<extra></extra>`;
                })
            });
        }

        // Tax
        if (taxAmount.some(v => v > 0)) {
            traces.push({
                x: data.periods,
                y: taxAmount,
                type: 'bar',
                name: 'Tax',
                marker: { color: '#ffc107' },
                hovertemplate: data.periods.map((period, i) => {
                    const pct = data.sales[i] ? (taxAmount[i] / data.sales[i] * 100).toFixed(1) : 0;
                    return `Tax: ${taxAmount[i].toFixed(0)} Cr (<b>${pct}%</b>)<extra></extra>`;
                })
            });
        }

        // Net Profit (what's left)
        if (data.net_profit && data.net_profit.some(v => v != null)) {
            traces.push({
                x: data.periods,
                y: data.net_profit,
                type: 'bar',
                name: 'Net Profit',
                marker: { color: '#198754' },
                hovertemplate: data.periods.map((period, i) => {
                    const pct = data.sales[i] ? ((data.net_profit[i] || 0) / data.sales[i] * 100).toFixed(1) : 0;
                    return `Net Profit: %{y:,.0f} Cr (<b>${pct}%</b>)<extra></extra>`;
                })
            });
        }

        const layout = {
            ...baseLayout,
            barmode: 'stack',
            yaxis: {
                ...baseLayout.yaxis,
                title: { text: 'Amount (Cr)', standoff: 10 },
                tickformat: ',.0f'
            },
            xaxis: {
                ...baseLayout.xaxis,
                tickangle: -45,
                range: [-0.5, data.periods.length - 0.5],
                dtick: 1
            },
            legend: {
                ...baseLayout.legend,
                y: -0.25
            }
        };

        Plotly.newPlot(containerId, traces, layout, chartConfig);
    }

    /**
     * Scroll chart containers to the right (show latest data)
     */
    function scrollChartsToRight() {
        const chartIds = ['sales-chart', 'profit-chart', 'margins-chart', 'eps-chart', 'breakdown-chart'];
        chartIds.forEach(id => {
            const container = document.getElementById(id);
            if (container && container.parentElement) {
                const parent = container.parentElement;
                parent.scrollLeft = parent.scrollWidth;
            }
        });
    }

    /**
     * Render all charts
     */
    function renderAllCharts(data) {
        renderSalesChart(data);
        renderProfitChart(data);
        renderMarginsChart(data);
        renderEPSChart(data);
        renderSalesBreakdownChart(data);

        // Scroll to right after charts render
        setTimeout(scrollChartsToRight, 100);
    }

    /**
     * Resize all charts (call on window resize)
     */
    function resizeCharts() {
        const chartIds = ['sales-chart', 'profit-chart', 'margins-chart', 'eps-chart', 'breakdown-chart'];
        chartIds.forEach(id => {
            const container = document.getElementById(id);
            if (container && container.data) {
                Plotly.Plots.resize(container);
            }
        });
    }

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(resizeCharts, 250);
    });

    // Public API
    return {
        renderAllCharts: renderAllCharts,
        renderSalesChart: renderSalesChart,
        renderProfitChart: renderProfitChart,
        renderMarginsChart: renderMarginsChart,
        renderEPSChart: renderEPSChart,
        renderSalesBreakdownChart: renderSalesBreakdownChart,
        resizeCharts: resizeCharts
    };
})();
