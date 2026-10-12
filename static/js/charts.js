/**
 * NexaBank Real-Time Performance Charts using Chart.js v4
 * Renders 4 dynamic time-series charts updating with the rolling 30-45 historical points.
 */

let chartTraffic = null;
let chartQueue = null;
let chartLatency = null;
let chartProcessedDropped = null;

const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 350,
        easing: 'easeInOutQuad'
    },
    interaction: {
        intersect: false,
        mode: 'index'
    },
    plugins: {
        legend: {
            position: 'top',
            labels: {
                color: '#94a3b8',
                font: { family: 'Inter', size: 11 },
                boxWidth: 12
            }
        },
        tooltip: {
            backgroundColor: '#0f1e38',
            borderColor: '#1e355b',
            borderWidth: 1,
            titleColor: '#f8fafc',
            bodyColor: '#94a3b8',
            titleFont: { family: 'JetBrains Mono' },
            bodyFont: { family: 'JetBrains Mono' }
        }
    },
    scales: {
        x: {
            ticks: {
                color: '#64748b',
                font: { family: 'JetBrains Mono', size: 10 },
                maxTicksLimit: 7
            },
            grid: {
                color: 'rgba(255, 255, 255, 0.04)'
            }
        },
        y: {
            beginAtZero: true,
            ticks: {
                color: '#64748b',
                font: { family: 'JetBrains Mono', size: 10 }
            },
            grid: {
                color: 'rgba(255, 255, 255, 0.05)'
            }
        }
    }
};

function initLiveCharts() {
    // 1. Traffic vs Capacity Chart
    const ctxTraffic = document.getElementById('chart-traffic-capacity')?.getContext('2d');
    if (ctxTraffic) {
        chartTraffic = new Chart(ctxTraffic, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Incoming Traffic (req/s)',
                        data: [],
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.12)',
                        borderWidth: 2,
                        tension: 0.35,
                        fill: true,
                        pointRadius: 1
                    },
                    {
                        label: 'Processing Capacity (20 req/s)',
                        data: [],
                        borderColor: '#f59e0b',
                        borderWidth: 1.8,
                        borderDash: [5, 5],
                        tension: 0,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    ...commonChartOptions.scales,
                    y: {
                        ...commonChartOptions.scales.y,
                        suggestedMax: 40
                    }
                }
            }
        });
    }

    // 2. Queue Length Chart
    const ctxQueue = document.getElementById('chart-queue-length')?.getContext('2d');
    if (ctxQueue) {
        chartQueue = new Chart(ctxQueue, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Queue Length (Items)',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.15)',
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true,
                        pointRadius: 1
                    },
                    {
                        label: 'Max Queue Threshold (40)',
                        data: [],
                        borderColor: '#ef4444',
                        borderWidth: 1.5,
                        borderDash: [4, 4],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    ...commonChartOptions.scales,
                    y: {
                        ...commonChartOptions.scales.y,
                        suggestedMax: 45
                    }
                }
            }
        });
    }

    // 3. Response Time (Latency) Chart
    const ctxLatency = document.getElementById('chart-response-time')?.getContext('2d');
    if (ctxLatency) {
        chartLatency = new Chart(ctxLatency, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Avg Latency (ms)',
                        data: [],
                        borderColor: '#a855f7',
                        backgroundColor: 'rgba(168, 85, 247, 0.12)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 1
                    }
                ]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    ...commonChartOptions.scales,
                    y: {
                        ...commonChartOptions.scales.y,
                        suggestedMax: 300
                    }
                }
            }
        });
    }

    // 4. Processed vs Dropped Requests Chart
    const ctxProcessedDropped = document.getElementById('chart-processed-dropped')?.getContext('2d');
    if (ctxProcessedDropped) {
        chartProcessedDropped = new Chart(ctxProcessedDropped, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Processed (req/s)',
                        data: [],
                        backgroundColor: 'rgba(16, 185, 129, 0.75)',
                        borderRadius: 3
                    },
                    {
                        label: 'Dropped by Rate Limiter',
                        data: [],
                        backgroundColor: 'rgba(239, 68, 68, 0.85)',
                        borderRadius: 3
                    }
                ]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    x: {
                        ...commonChartOptions.scales.x,
                        stacked: true
                    },
                    y: {
                        ...commonChartOptions.scales.y,
                        stacked: true,
                        suggestedMax: 30
                    }
                }
            }
        });
    }
}

// Global update callback invoked by network.js during each poll
window.updateLiveCharts = function(history, currentData) {
    if (!history || history.length === 0) return;

    const labels = history.map(item => item.time);
    const incomingData = history.map(item => item.incoming_rate);
    const capacityData = history.map(item => item.capacity || 20);
    const queueData = history.map(item => item.queue_length);
    const maxQueueData = history.map(() => 40);
    const latencyData = history.map(item => item.latency_ms);
    const processedData = history.map(item => item.processing_rate);
    const droppedData = history.map(item => item.dropped_count);

    if (chartTraffic) {
        chartTraffic.data.labels = labels;
        chartTraffic.data.datasets[0].data = incomingData;
        chartTraffic.data.datasets[1].data = capacityData;
        chartTraffic.update('none');
    }

    if (chartQueue) {
        chartQueue.data.labels = labels;
        chartQueue.data.datasets[0].data = queueData;
        chartQueue.data.datasets[1].data = maxQueueData;
        chartQueue.update('none');
    }

    if (chartLatency) {
        chartLatency.data.labels = labels;
        chartLatency.data.datasets[0].data = latencyData;
        chartLatency.update('none');
    }

    if (chartProcessedDropped) {
        chartProcessedDropped.data.labels = labels;
        chartProcessedDropped.data.datasets[0].data = processedData;
        chartProcessedDropped.data.datasets[1].data = droppedData;
        chartProcessedDropped.update('none');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    initLiveCharts();
});
