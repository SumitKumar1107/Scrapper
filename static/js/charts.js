/**
 * Charts Module
 * Handles Plotly chart rendering for financial data
 */
const ChartsModule = (function() {
    // Chart configuration
    const chartConfig = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: 'financial_chart',
            height: 600,
            width: 1200,
            scale: 2
        }
    };

    // Base layout configuration
    const baseLayout = {
        margin: { t: 40, r: 30, b: 60, l: 70 },
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.15,
            x: 0.5,
            xanchor: 'center'
        },
        hovermode: 'x unified',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            family: 'system-ui, -apple-system, sans-serif',
            size: 12
        },
        xaxis: {
            showgrid: false,
            showline: true,
            linecolor: '#dee2e6'
        },
        yaxis: {
            showgrid: true,
            gridcolor: '#f0f0f0',
            showline: true,
            linecolor: '#dee2e6',
            zeroline: true,
            zerolinecolor: '#dee2e6'
        }
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

    /**
     * Render Sales/Revenue bar chart
     */
    function renderSalesChart(data, containerId = 'sales-chart') {
        if (!data.periods || data.periods.length === 0) {
            showNoData(containerId);
            return;
        }

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
                tickangle: -45
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
                tickangle: -45
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

        // Operating Profit Margin
        const opmTrace = {
            x: data.periods,
            y: data.opm_percent,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'OPM %',
            line: { color: colors.success, width: 2 },
            marker: { size: 8 },
            hovertemplate: '<b>%{x}</b><br>OPM: %{y:.1f}%<extra></extra>'
        };

        // Calculate Net Profit Margin
        const npmPercent = data.periods.map((_, i) => {
            if (data.sales[i] && data.net_profit[i] && data.sales[i] !== 0) {
                return ((data.net_profit[i] / data.sales[i]) * 100);
            }
            return null;
        });

        const npmTrace = {
            x: data.periods,
            y: npmPercent,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'NPM %',
            line: { color: colors.purple, width: 2 },
            marker: { size: 8 },
            hovertemplate: '<b>%{x}</b><br>NPM: %{y:.1f}%<extra></extra>'
        };

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
                tickangle: -45
            }
        };

        Plotly.newPlot(containerId, [opmTrace, npmTrace], layout, chartConfig);
    }

    /**
     * Render EPS line chart with area fill
     */
    function renderEPSChart(data, containerId = 'eps-chart') {
        if (!data.periods || data.periods.length === 0) {
            showNoData(containerId);
            return;
        }

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
                tickangle: -45
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
     * Render all charts
     */
    function renderAllCharts(data) {
        renderSalesChart(data);
        renderProfitChart(data);
        renderMarginsChart(data);
        renderEPSChart(data);
    }

    /**
     * Resize all charts (call on window resize)
     */
    function resizeCharts() {
        const chartIds = ['sales-chart', 'profit-chart', 'margins-chart', 'eps-chart'];
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
        resizeCharts: resizeCharts
    };
})();
