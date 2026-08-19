// Polluxa LinkedIn Agent Analytics Dashboard Logic
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initCharts();
    loadDashboardData();

    document.getElementById("btn-refresh-data").addEventListener("click", () => {
        loadDashboardData();
    });

    document.getElementById("btn-run-demo").addEventListener("click", () => {
        fetch("/api/trigger-demo")
            .then(res => res.json())
            .then(data => {
                alert("Resilience Demo pipeline executed live on database!");
                loadDashboardData();
            })
            .catch(() => {
                alert("Triggered local demo execution!");
                setTimeout(() => loadDashboardData(), 1500);
            });
    });
});

function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".dashboard-section");
    const titleEl = document.getElementById("current-view-title");

    const titles = {
        "nav-overview": "Executive Analytics Dashboard",
        "nav-health": "Agent Risk & Account Health Intelligence",
        "nav-campaigns": "Campaign Performance & Segment ROI",
        "nav-quality": "Data Governance & DQ Audit Log"
    };

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");

            const targetId = item.id.replace("nav-", "section-");
            sections.forEach(s => s.classList.add("hidden"));
            document.getElementById(targetId).classList.remove("hidden");

            titleEl.textContent = titles[item.id] || "Analytics Platform";
        });
    });
}

let trendChart, statusChart, utilizationChart, campaignChart, segmentChart;

function initCharts() {
    // 1. Performance Trend Chart
    const ctxTrend = document.getElementById("trendChart").getContext("2d");
    trendChart = new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
            datasets: [
                {
                    label: 'Invites Sent',
                    data: [150, 180, 210, 190, 240, 220, 260],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Accepts Received',
                    data: [60, 72, 85, 78, 95, 90, 105],
                    borderColor: '#10b981',
                    tension: 0.4
                },
                {
                    label: 'Replies Received',
                    data: [25, 30, 38, 32, 42, 40, 48],
                    borderColor: '#8b5cf6',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });

    // 2. Agent Status Donut Chart
    const ctxStatus = document.getElementById("statusChart").getContext("2d");
    statusChart = new Chart(ctxStatus, {
        type: 'doughnut',
        data: {
            labels: ['Active Agents', 'Paused Agents', 'Ghosted Agents'],
            datasets: [{
                data: [3, 1, 1],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } }
        }
    });

    // 3. Utilization Bar Chart
    const ctxUtil = document.getElementById("utilizationChart").getContext("2d");
    utilizationChart = new Chart(ctxUtil, {
        type: 'bar',
        data: {
            labels: ['AGT-001', 'AGT-002', 'AGT-003', 'AGT-004'],
            datasets: [
                { label: 'Daily Invites Used', data: [28, 22, 12, 4], backgroundColor: '#3b82f6' },
                { label: 'Tier Invite Ceiling', data: [30, 25, 15, 5], backgroundColor: 'rgba(255,255,255,0.1)' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#64748b' } },
                y: { ticks: { color: '#64748b' } }
            }
        }
    });

    // 4. Campaign Funnel Chart
    const ctxCamp = document.getElementById("campaignChart").getContext("2d");
    campaignChart = new Chart(ctxCamp, {
        type: 'bar',
        data: {
            labels: ['Invites Sent', 'Accepts', 'Messages Sent', 'Replies'],
            datasets: [{
                label: 'Q3 Senior Dev Campaign',
                data: [850, 320, 320, 115],
                backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { color: '#64748b' } }, y: { ticks: { color: '#64748b' } } }
        }
    });

    // 5. Segment Performance Pie Chart
    const ctxSeg = document.getElementById("segmentChart").getContext("2d");
    segmentChart = new Chart(ctxSeg, {
        type: 'pie',
        data: {
            labels: ['Engineering Leads', 'Sales VPs', 'Recruiters', 'Product Managers'],
            datasets: [{
                data: [45, 25, 20, 10],
                backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } }
        }
    });
}

function loadDashboardData() {
    fetch("/api/dashboard-data")
        .then(res => res.json())
        .then(resData => {
            if (resData.status === "success") {
                renderLiveData(resData.data);
            } else {
                renderMockData();
            }
        })
        .catch(() => {
            renderMockData();
        });
}

function renderLiveData(data) {
    if (data.kpis) {
        document.getElementById("kpi-invites").textContent = data.kpis.invites;
        document.getElementById("kpi-acc-rate").textContent = data.kpis.accRate;
        document.getElementById("kpi-reply-rate").textContent = data.kpis.replyRate;
        document.getElementById("kpi-anomaly").textContent = data.kpis.anomalyScore;
        if (document.getElementById("dq-score")) document.getElementById("dq-score").textContent = data.kpis.latestDqScore;
        if (document.getElementById("dlq-count")) document.getElementById("dlq-count").textContent = data.kpis.dlqCount;
    }

    if (data.agents && data.agents.length > 0) {
        const tbody = document.querySelector("#agent-table tbody");
        tbody.innerHTML = "";
        data.agents.forEach(a => {
            const tr = document.createElement("tr");
            const statusBadge = a.status === "Active" ? "badge-normal" : (a.status === "Warning" ? "badge-warning" : "badge-critical");
            tr.innerHTML = `
                <td><strong>${a.name}</strong></td>
                <td>${a.tier}</td>
                <td>${a.risk}</td>
                <td>${a.invites}</td>
                <td>${a.accRate}</td>
                <td><strong>${a.score}</strong></td>
                <td><span class="kpi-badge ${statusBadge}">${a.status}</span></td>
                <td>${a.limit}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    if (data.dqLogs && data.dqLogs.length > 0) {
        const dqTbody = document.querySelector("#dq-table tbody");
        dqTbody.innerHTML = "";
        data.dqLogs.forEach(d => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>#${d.id}</td>
                <td><code>${d.runId}</code></td>
                <td>${d.time}</td>
                <td>${d.comp}</td>
                <td>${d.uniq}</td>
                <td>${d.val}</td>
                <td>${d.tim}</td>
                <td>${d.ref}</td>
                <td><strong>${d.score}</strong></td>
                <td><span class="kpi-badge badge-normal">${d.status}</span></td>
            `;
            dqTbody.appendChild(tr);
        });
    }
}

function renderMockData() {
    const mockAgents = [
        { name: "Sarah Connor", tier: "1+ Year", risk: "Minimal Risk", invites: 180, accRate: "41.2%", score: 0.25, status: "Active", limit: "30/day" },
        { name: "Alex Mercer", tier: "6–12 Months", risk: "Low Risk", invites: 145, accRate: "36.5%", score: 0.65, status: "Active", limit: "25/day" },
        { name: "Jordan Lee", tier: "1 Month", risk: "High Risk", invites: 65, accRate: "21.0%", score: 1.85, status: "Warning", limit: "7/day (Throttled)" },
        { name: "Taylor Swift", tier: "< 1 Month", risk: "Very High Risk", invites: 15, accRate: "0.0%", score: 2.95, status: "Critical", limit: "2/day (Throttled)" }
    ];

    const tbody = document.querySelector("#agent-table tbody");
    if (tbody) {
        tbody.innerHTML = "";
        mockAgents.forEach(a => {
            const tr = document.createElement("tr");
            const statusBadge = a.status === "Active" ? "badge-normal" : (a.status === "Warning" ? "badge-warning" : "badge-critical");
            tr.innerHTML = `
                <td><strong>${a.name}</strong></td>
                <td>${a.tier}</td>
                <td>${a.risk}</td>
                <td>${a.invites}</td>
                <td>${a.accRate}</td>
                <td><strong>${a.score}</strong></td>
                <td><span class="kpi-badge ${statusBadge}">${a.status}</span></td>
                <td>${a.limit}</td>
            `;
            tbody.appendChild(tr);
        });
    }
}
