/**
 * NexaBank Global Real-Time Network Poller & Pipeline Coordinator
 * Polls /api/network-stats every 1000ms to update live UI cards, navbar, pipeline flow, and event logs.
 */

let lastLogCount = 0;

async function fetchNetworkStats() {
    try {
        const response = await fetch('/api/network-stats');
        if (!response.ok) return;
        const data = await response.json();

        // 1. Update Global Top Navbar Status
        updateNavbarStatus(data);

        // 2. Update Dashboard Mini Cards (if present)
        updateDashboardCards(data);

        // 3. Update Network Monitor Big Cards (if present)
        updateNetworkMonitorCards(data);

        // 4. Update Pipeline Diagram Highlights (if present)
        updatePipelineDiagram(data);

        // 5. Update Full Demo Progress & Banner (if present)
        updateFullDemoBanner(data.simulation);

        // 6. Update Terminal Event Log (if present)
        updateTerminalLog(data.event_logs);

        // 7. Notify Chart.js instance (if active)
        if (typeof window.updateLiveCharts === 'function') {
            window.updateLiveCharts(data.history, data);
        }

    } catch (err) {
        console.warn('Network stats polling paused or interrupted:', err);
    }
}

function updateNavbarStatus(data) {
    const pulseDot = document.getElementById('nav-pulse-dot');
    const statusText = document.getElementById('nav-status-text');
    if (pulseDot && statusText) {
        statusText.textContent = `NETWORK: ${data.congestion_level}`;
        statusText.style.color = data.status_color;
        pulseDot.style.backgroundColor = data.status_color;
        pulseDot.style.boxShadow = `0 0 10px ${data.status_color}`;
    }
    
    // Transfer page live status badge
    const transferStatus = document.getElementById('transfer-live-status');
    if (transferStatus) {
        transferStatus.textContent = `NETWORK: ${data.congestion_level}`;
        transferStatus.className = `badge badge-${data.congestion_level.toLowerCase()}`;
    }
}

function updateDashboardCards(data) {
    const elStatus = document.getElementById('dash-network-status');
    if (!elStatus) return;

    elStatus.textContent = data.congestion_level;
    elStatus.style.color = data.status_color;

    const subtextEl = document.getElementById('dash-status-subtext');
    if (subtextEl) {
        const subtexts = {
            "NORMAL": "Operating within 20 req/s capacity",
            "MODERATE": "Incoming load slightly exceeds capacity",
            "CONGESTED": "Traffic surge! Queuing active",
            "CRITICAL": "Buffer saturated! Rate limiter shedding load"
        };
        subtextEl.textContent = subtexts[data.congestion_level] || "Processing";
    }

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setVal('dash-incoming-rate', data.incoming_rate.toFixed(1));
    setVal('dash-processing-rate', data.processing_rate.toFixed(1));
    setVal('dash-queue-len', `${data.queue_length} / 40`);
    setVal('dash-avg-latency', `${data.avg_response_time} ms`);
    setVal('dash-dropped-count', data.total_dropped);
}

function updateNetworkMonitorCards(data) {
    const elStatus = document.getElementById('mon-network-status');
    if (!elStatus) return;

    elStatus.textContent = data.congestion_level;
    elStatus.style.color = data.status_color;

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setVal('mon-incoming-rate', `${data.incoming_rate.toFixed(1)} req/s`);
    setVal('mon-processing-rate', `${data.processing_rate.toFixed(1)} req/s`);
    setVal('mon-queue-len', `${data.queue_length} items`);
    setVal('mon-avg-latency', `${data.avg_response_time} ms`);
    setVal('mon-dropped-count', data.total_dropped);

    const subtextEl = document.getElementById('mon-status-subtext');
    if (subtextEl) {
        if (data.rate_limiter_active) {
            subtextEl.textContent = "Rate Limiter ACTIVE (Load Shedding)";
            subtextEl.style.color = "var(--status-critical)";
        } else {
            subtextEl.textContent = "Operating within capacity boundaries";
            subtextEl.style.color = "var(--text-muted)";
        }
    }
}

function updatePipelineDiagram(data) {
    const pipeBadge = document.getElementById('pipeline-status-badge');
    if (!pipeBadge) return;

    pipeBadge.textContent = `STATE: ${data.congestion_level}`;
    pipeBadge.className = `badge badge-${data.congestion_level.toLowerCase()}`;

    // Active node highlight sequence
    const nodeLimiter = document.getElementById('node-limiter');
    const nodeQueue = document.getElementById('node-queue');
    const nodeDetector = document.getElementById('node-detector');

    if (nodeLimiter && nodeQueue && nodeDetector) {
        if (data.rate_limiter_active) {
            nodeLimiter.style.borderColor = 'var(--status-critical)';
            nodeLimiter.style.boxShadow = '0 0 16px rgba(239, 68, 68, 0.4)';
        } else {
            nodeLimiter.style.borderColor = 'var(--border-color)';
            nodeLimiter.style.boxShadow = 'none';
        }

        if (data.queue_length > 10) {
            nodeQueue.style.borderColor = 'var(--status-moderate)';
            nodeQueue.style.boxShadow = '0 0 16px rgba(245, 158, 11, 0.4)';
        } else {
            nodeQueue.style.borderColor = 'var(--border-color)';
            nodeQueue.style.boxShadow = 'none';
        }
    }
}

function updateFullDemoBanner(sim) {
    if (!sim) return;

    const stageLabel = document.getElementById('demo-stage-label');
    const progressBar = document.getElementById('demo-progress-bar');
    const percentageText = document.getElementById('demo-percentage-text');
    const simStateText = document.getElementById('sim-state-text');
    const demoBtn = document.getElementById('btn-run-full-demo');

    if (stageLabel) {
        stageLabel.textContent = sim.demo_stage || (sim.is_running ? `RUNNING (${sim.current_level})` : 'IDLE');
    }

    if (progressBar) {
        progressBar.style.width = `${sim.demo_progress}%`;
    }

    if (percentageText) {
        percentageText.textContent = `Progress: ${sim.demo_progress}%`;
    }

    if (simStateText) {
        simStateText.textContent = sim.full_demo_active ? `DEMO: ${sim.demo_stage}` : (sim.is_running ? sim.current_level : 'IDLE');
        simStateText.style.color = sim.is_running ? 'var(--status-normal)' : 'var(--text-secondary)';
    }

    if (demoBtn && !sim.full_demo_active) {
        demoBtn.disabled = false;
        demoBtn.innerHTML = '<i class="fa-solid fa-play"></i> RUN FULL DEMO';
    }
}

function updateTerminalLog(logs) {
    const terminal = document.getElementById('terminal-event-log');
    if (!terminal || !logs || logs.length === 0) return;

    // Only re-render if log items changed
    if (logs.length === lastLogCount) return;
    lastLogCount = logs.length;

    terminal.innerHTML = '';
    logs.forEach(item => {
        const line = document.createElement('div');
        line.className = `terminal-line ${item.level}`;
        line.innerHTML = `<span class="terminal-time">[${item.time}]</span> <span class="terminal-msg">${item.message}</span>`;
        terminal.appendChild(line);
    });

    // Auto-scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
}

// Start polling on DOM load
document.addEventListener('DOMContentLoaded', () => {
    fetchNetworkStats();
    setInterval(fetchNetworkStats, 1000);
});
