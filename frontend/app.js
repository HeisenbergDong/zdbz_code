const API_BASE = '/api';
const statusMap = {
    'pending': { label: '待处理', class: 'status-pending' },
    'processing': { label: '处理中', class: 'status-processing' },
    'completed': { label: '已完成', class: 'status-completed' }
};
const priorityMap = {
    'high': { label: '高', class: 'priority-high' },
    'medium': { label: '中', class: 'priority-medium' },
    'low': { label: '低', class: 'priority-low' }
};

let currentStatusFilter = '';

async function fetchTickets(status = '') {
    let url = `${API_BASE}/tickets`;
    if (status) {
        url += `?status=${status}`;
    }
    const response = await fetch(url);
    return await response.json();
}

async function fetchStats() {
    const response = await fetch(`${API_BASE}/tickets/stats`);
    return await response.json();
}

async function createTicket(ticketData) {
    const response = await fetch(`${API_BASE}/tickets`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(ticketData)
    });
    return await response.json();
}

async function updateTicketStatus(ticketId, newStatus) {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    });
    return await response.json();
}

function renderStats(stats) {
    document.getElementById('totalCount').textContent = stats.total || 0;
    document.getElementById('pendingCount').textContent = stats.pending || 0;
    document.getElementById('processingCount').textContent = stats.processing || 0;
    document.getElementById('completedCount').textContent = stats.completed || 0;
}

function renderTickets(tickets) {
    const ticketList = document.getElementById('ticketList');
    
    if (tickets.length === 0) {
        ticketList.innerHTML = '<div class="empty-state">暂无工单数据</div>';
        return;
    }

    ticketList.innerHTML = tickets.map(ticket => {
        const status = statusMap[ticket.status] || statusMap.pending;
        const priority = priorityMap[ticket.priority] || priorityMap.medium;
        
        const availableStatuses = ['pending', 'processing', 'completed'].filter(s => s !== ticket.status);
        const statusButtons = availableStatuses.map(s => {
            const sInfo = statusMap[s];
            return `<button class="btn-status ${s}" onclick="handleStatusChange('${ticket.id}', '${s}')">${sInfo.label}</button>`;
        }).join('');

        return `
            <div class="ticket-card ${ticket.status}">
                <div class="ticket-header">
                    <span class="ticket-id">${ticket.id}</span>
                    <span class="ticket-priority ${priority.class}">${priority.label}</span>
                </div>
                <div class="ticket-title">${ticket.title}</div>
                <div class="ticket-meta">
                    <span>👤 ${ticket.assignee}</span>
                    <span>🕐 ${ticket.updated_at}</span>
                </div>
                <div class="ticket-actions">
                    <span class="status-label ${status.class}">${status.label}</span>
                    ${statusButtons}
                </div>
            </div>
        `;
    }).join('');
}

async function handleStatusChange(ticketId, newStatus) {
    const result = await updateTicketStatus(ticketId, newStatus);
    if (result.success) {
        await refreshData();
    } else {
        alert('状态更新失败：' + (result.errors || []).join(', '));
    }
}

async function refreshData() {
    const [tickets, stats] = await Promise.all([
        fetchTickets(currentStatusFilter),
        fetchStats()
    ]);
    renderTickets(tickets);
    renderStats(stats);
}

function setupEventListeners() {
    document.getElementById('statusFilter').addEventListener('change', async (e) => {
        currentStatusFilter = e.target.value;
        const tickets = await fetchTickets(currentStatusFilter);
        renderTickets(tickets);
    });

    document.getElementById('addTicketBtn').addEventListener('click', () => {
        document.getElementById('ticketModal').classList.add('show');
    });

    document.getElementById('closeModal').addEventListener('click', () => {
        document.getElementById('ticketModal').classList.remove('show');
    });

    document.getElementById('cancelBtn').addEventListener('click', () => {
        document.getElementById('ticketModal').classList.remove('show');
    });

    document.getElementById('ticketModal').addEventListener('click', (e) => {
        if (e.target.id === 'ticketModal') {
            document.getElementById('ticketModal').classList.remove('show');
        }
    });

    document.getElementById('ticketForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            title: document.getElementById('title').value,
            priority: document.getElementById('priority').value,
            assignee: document.getElementById('assignee').value
        };

        const result = await createTicket(formData);
        
        if (result.success) {
            document.getElementById('ticketForm').reset();
            document.getElementById('ticketModal').classList.remove('show');
            currentStatusFilter = '';
            document.getElementById('statusFilter').value = '';
            await refreshData();
        } else {
            alert('创建失败：' + (result.errors || []).join(', '));
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    refreshData();
});
