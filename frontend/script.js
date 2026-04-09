document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const chatContainer = document.getElementById('chat-container');
    const modal = document.getElementById('decision-modal');
    
    let isRunning = false;

    // Fetch dynamic telemetry metrics
    fetchDashboardData();

    startBtn.addEventListener('click', () => {
        if (isRunning) return;
        isRunning = true;
        startBtn.textContent = 'Simulation Running...';
        startBtn.disabled = true;
        
        chatContainer.innerHTML = ''; // Clear placeholder
        
        const evtSource = new EventSource("/api/start");

        evtSource.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.message === "[DONE]") {
                evtSource.close();
                startBtn.textContent = 'Simulation Complete';
                return;
            }

            if (data.finalData) {
                renderFinalDecision(data.finalData);
                return;
            }

            renderMessage(data.sender, data.message);
        };
        
        evtSource.onerror = function(err) {
            console.error("EventSource failed:", err);
            evtSource.close();
            startBtn.textContent = 'Error Occurred';
        };
    });
});

function fetchDashboardData() {
    fetch('/api/dashboard-data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('val-latency').textContent = data.latency;
            document.getElementById('val-success').textContent = data.success;
            document.getElementById('val-tickets').textContent = data.tickets;
            
            const latVal = parseInt(data.latency);
            const succVal = parseInt(data.success);
            
            setCardStatus('card-latency', 'trend-latency', latVal > 300 ? (latVal >= 500 ? 'negative' : 'warning') : 'positive', latVal >= 500 ? '↑ Crashing' : (latVal > 300 ? '↑ Elevated' : '↓ Healthy'));
            setCardStatus('card-success', 'trend-success', succVal < 90 ? (succVal <= 75 ? 'negative' : 'warning') : 'positive', succVal <= 75 ? '↓ Dropping' : (succVal < 95 ? '↓ Sinking' : '↑ Perfect'));
            setCardStatus('card-tickets', 'trend-tickets', data.tickets > 300 ? 'warning' : 'positive', data.tickets > 300 ? '↑ High Volume' : '↓ Standard');
            
            document.getElementById('feedback-list').innerHTML = `<li>"${data.feedback}"</li>`;
            document.querySelector('.release-notes').innerHTML = `<h3>Launch Context</h3><p>${data.notes}</p>`;
        });
}

function setCardStatus(cardId, trendId, status, trendText) {
    const card = document.getElementById(cardId);
    card.className = `stat-card ${status}`;
    document.getElementById(trendId).textContent = trendText;
}

function renderMessage(sender, message) {
    const chatContainer = document.getElementById('chat-container');
    
    const msgDiv = document.createElement('div');
    // Map role string to css class
    let roleClass = 'role-PM';
    if (sender === 'System') roleClass = 'role-System';
    if (sender === 'Data Analyst') roleClass = 'role-Data';
    if (sender === 'Marketing/Comms') roleClass = 'role-Marketing';
    if (sender === 'Risk/Critic') roleClass = 'role-Risk';
    if (sender === 'DevOps Lead') roleClass = 'role-DevOps';

    msgDiv.className = `chat-msg ${roleClass}`;
    
    const header = document.createElement('div');
    header.className = 'msg-header';
    header.textContent = sender;
    
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    
    // Auto-link tools if present in string (visual sugar)
    let formattedHTML = message
        .replace(/get_metric_trend/g, '<code style="color:var(--purple)">get_metric_trend</code>')
        .replace(/analyze_sentiment/g, '<code style="color:var(--purple)">analyze_sentiment</code>')
        .replace(/get_release_notes/g, '<code style="color:var(--purple)">get_release_notes</code>');

    bubble.innerHTML = formattedHTML;
    
    msgDiv.appendChild(header);
    msgDiv.appendChild(bubble);
    chatContainer.appendChild(msgDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function renderFinalDecision(data) {
    const modal = document.getElementById('decision-modal');
    
    // Set Badge
    const badge = document.getElementById('decision-badge');
    badge.textContent = data.decision.toUpperCase();
    badge.className = 'badge'; // reset
    if (data.decision.toLowerCase().includes('roll back') || data.decision.toLowerCase().includes('rollback')) {
        badge.classList.add('rollback');
    } else if (data.decision.toLowerCase().includes('pause')) {
        badge.classList.add('pause');
    } else {
        badge.classList.add('proceed');
    }
    
    document.getElementById('decision-rationale').textContent = data.rationale;
    
    // Action Plan
    const actionList = document.getElementById('action-plan-list');
    actionList.innerHTML = '';
    (data.action_plan || []).forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>[${item.owner}]</strong> ${item.action}`;
        actionList.appendChild(li);
    });
    
    // Risks
    const riskList = document.getElementById('risk-list');
    riskList.innerHTML = '';
    (data.risk_register || []).forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>Risk:</strong> ${item.risk}<br><span style="color:var(--success)"><em>Mitigation:</em> ${item.mitigation}</span>`;
        riskList.appendChild(li);
    });
    
    // Comms
    if (data.communication_plan) {
        document.getElementById('comm-internal').textContent = data.communication_plan.internal || 'N/A';
        document.getElementById('comm-external').textContent = data.communication_plan.external || 'N/A';
    }
    
    document.getElementById('confidence-score').textContent = data.confidence_score;
    
    // Show Modal with slight delay for dramatic effect
    setTimeout(() => {
        modal.classList.remove('hidden');
    }, 1000);
}

function closeModal() {
    document.getElementById('decision-modal').classList.add('hidden');
}
