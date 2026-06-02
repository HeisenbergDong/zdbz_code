const API_BASE = '/api';

let meta = { statuses: [], priorities: [], groups: [], transitions: {} };
let filters = { status: '', priority: '', group: '', keyword: '' };

const STATUS_LABELS = {
    new: '新建',
    assigned: '已指派',
    in_progress: '处理中',
    blocked: '阻塞',
    resolved: '已解决',
    closed: '已关闭'
};

const GROUP_LABELS = {
    dormitory: '宿舍管理',
    logistics: '后勤保障',
    it_center: '信息中心'
};

const PRIORITY_LABELS = {
    low: '低',
    medium: '中',
    high: '高'
};

async function fetchMeta() {
    const res = await fetch(`${API_BASE}/meta`);
    meta = await res.json();
    meta.transitions = meta.transitions || {};
    populateFilterOptions();
    populateCreateFormOptions();
}

function populateFilterOptions() {
    const statusSelect = document.getElementById('filterStatus');
    statusSelect.innerHTML = '<option value="">全部</option>';
    meta.statuses.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.value;
        opt.textContent = STATUS_LABELS[s.value] || s.label;
        statusSelect.appendChild(opt);
    });

    const prioritySelect = document.getElementById('filterPriority');
    prioritySelect.innerHTML = '<option value="">全部</option>';
    meta.priorities.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.value;
        opt.textContent = PRIORITY_LABELS[p.value] || p.label;
        prioritySelect.appendChild(opt);
    });

    const groupSelect = document.getElementById('filterGroup');
    groupSelect.innerHTML = '<option value="">全部</option>';
    meta.groups.forEach(g => {
        const opt = document.createElement('option');
        opt.value = g.value;
        opt.textContent = GROUP_LABELS[g.value] || g.label;
        groupSelect.appendChild(opt);
    });
}

function populateCreateFormOptions() {
    const prioritySelect = document.getElementById('createPriority');
    prioritySelect.innerHTML = '';
    meta.priorities.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.value;
        opt.textContent = PRIORITY_LABELS[p.value] || p.label;
        if (p.value === 'medium') opt.selected = true;
        prioritySelect.appendChild(opt);
    });

    const groupSelect = document.getElementById('createGroup');
    groupSelect.innerHTML = '';
    meta.groups.forEach(g => {
        const opt = document.createElement('option');
        opt.value = g.value;
        opt.textContent = GROUP_LABELS[g.value] || g.label;
        groupSelect.appendChild(opt);
    });
}

async function fetchTickets() {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.priority) params.set('priority', filters.priority);
    if (filters.group) params.set('group', filters.group);
    if (filters.keyword) params.set('keyword', filters.keyword);
    const qs = params.toString();
    const url = `${API_BASE}/tickets${qs ? '?' + qs : ''}`;
    const res = await fetch(url);
    return await res.json();
}

async function fetchStats() {
    const res = await fetch(`${API_BASE}/tickets/stats`);
    return await res.json();
}

async function createTicket(data) {
    const res = await fetch(`${API_BASE}/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return await res.json();
}

async function assignTicket(id, assignee) {
    const res = await fetch(`${API_BASE}/tickets/${id}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assignee })
    });
    return await res.json();
}

async function updateTicketStatus(id, status) {
    const res = await fetch(`${API_BASE}/tickets/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    });
    return await res.json();
}

function renderStats(stats) {
    document.getElementById('statTotal').textContent = stats.total || 0;
    document.getElementById('statPending').textContent = stats.pending_total || 0;
    document.getElementById('statOverdue').textContent = stats.overdue || 0;
    document.getElementById('statNearOverdue').textContent = stats.near_overdue || 0;
    const byGroup = stats.by_group || {};
    document.getElementById('statGroupDormitory').textContent = byGroup.dormitory || 0;
    document.getElementById('statGroupLogistics').textContent = byGroup.logistics || 0;
    document.getElementById('statGroupIt').textContent = byGroup.it_center || 0;
}

function renderTickets(tickets) {
    const list = document.getElementById('ticketList');
    if (!tickets.length) {
        list.innerHTML = '<div class="empty-state">暂无工单数据</div>';
        return;
    }
    list.innerHTML = tickets.map(t => {
        const statusLabel = STATUS_LABELS[t.status] || t.status;
        const priorityLabel = PRIORITY_LABELS[t.priority] || t.priority;
        const groupLabel = GROUP_LABELS[t.group] || t.group;
        const allowedTransitions = meta.transitions[t.status] || [];

        const transitionBtns = allowedTransitions.map(target => {
            const targetLabel = STATUS_LABELS[target] || target;
            return `<button class="btn-transition target-${target}" onclick="handleTransition('${t.id}','${target}')">${targetLabel}</button>`;
        }).join('');

        const assignBtn = t.status !== 'closed'
            ? `<button class="btn-assign" onclick="handleAssign('${t.id}')">指派</button>`
            : '';

        const auditEntries = (t.audit_log || []).map(e => {
            const time = e.time || '';
            const action = e.action || '';
            const detail = e.detail || '';
            const operator = e.operator || '';
            return `<div class="audit-entry">
                <span class="audit-time">${time}</span>
                <span class="audit-detail">[${action}] ${detail} <span class="audit-operator">${operator}</span></span>
            </div>`;
        }).join('');

        const auditSection = t.audit_log && t.audit_log.length
            ? `<button class="audit-toggle" onclick="toggleAudit('${t.id}')">审计日志</button>
               <div class="audit-log" id="audit-${t.id}">
                   <div class="audit-timeline">${auditEntries}</div>
               </div>`
            : '';

        return `<div class="ticket-card status-${t.status}">
            <div class="ticket-header">
                <span class="ticket-id">${t.id}</span>
                <div class="ticket-badges">
                    <span class="badge badge-status-${t.status}">${statusLabel}</span>
                    <span class="badge badge-priority-${t.priority}">${priorityLabel}</span>
                </div>
            </div>
            <div class="ticket-title">${escapeHtml(t.title)}</div>
            <div class="ticket-meta">
                <span>${groupLabel}</span>
                <span>${t.location || '-'}</span>
                <span>${t.assignee || '未指派'}</span>
                <span>${t.contact || '-'}</span>
                <span>${t.deadline || '无截止'}</span>
                <span>${t.updated_at}</span>
            </div>
            <div class="ticket-actions">
                ${transitionBtns}
                ${assignBtn}
            </div>
            ${auditSection}
        </div>`;
    }).join('');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

async function refreshData() {
    const [tickets, stats] = await Promise.all([fetchTickets(), fetchStats()]);
    renderTickets(tickets);
    renderStats(stats);
}

async function handleTransition(id, newStatus) {
    const result = await updateTicketStatus(id, newStatus);
    if (result.success) {
        await refreshData();
    } else {
        alert('状态更新失败：' + (result.errors || []).join(', '));
    }
}

function handleAssign(id) {
    document.getElementById('assignTicketId').value = id;
    document.getElementById('assignAssignee').value = '';
    document.getElementById('assignModal').classList.add('show');
}

function toggleAudit(id) {
    const el = document.getElementById('audit-' + id);
    if (el) {
        el.classList.toggle('visible');
        const btn = el.previousElementSibling;
        if (btn && btn.classList.contains('audit-toggle')) {
            btn.classList.toggle('active');
        }
    }
}

function openModal(modalId) {
    document.getElementById(modalId).classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

function showWarnings(warnings) {
    const section = document.getElementById('warningSection');
    const content = document.getElementById('warningContent');
    if (!warnings || !warnings.length) {
        section.style.display = 'none';
        return;
    }
    content.innerHTML = warnings.map(w =>
        `<div class="warning-item">相似工单 ${w.id}: "${escapeHtml(w.title)}" (相似度: ${w.similarity})</div>`
    ).join('');
    section.style.display = 'block';
}

function setupEventListeners() {
    document.getElementById('filterStatus').addEventListener('change', e => {
        filters.status = e.target.value;
        refreshData();
    });

    document.getElementById('filterPriority').addEventListener('change', e => {
        filters.priority = e.target.value;
        refreshData();
    });

    document.getElementById('filterGroup').addEventListener('change', e => {
        filters.group = e.target.value;
        refreshData();
    });

    let keywordTimer = null;
    document.getElementById('filterKeyword').addEventListener('input', e => {
        filters.keyword = e.target.value;
        clearTimeout(keywordTimer);
        keywordTimer = setTimeout(() => refreshData(), 300);
    });

    document.getElementById('createTicketBtn').addEventListener('click', () => {
        document.getElementById('createForm').reset();
        openModal('createModal');
    });

    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(btn.getAttribute('data-modal'));
        });
    });

    document.querySelectorAll('.modal-cancel').forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(btn.getAttribute('data-modal'));
        });
    });

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', e => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });

    document.getElementById('createForm').addEventListener('submit', async e => {
        e.preventDefault();
        const deadline = document.getElementById('createDeadline').value;
        const data = {
            title: document.getElementById('createTitle').value,
            priority: document.getElementById('createPriority').value,
            group: document.getElementById('createGroup').value,
            assignee: document.getElementById('createAssignee').value,
            location: document.getElementById('createLocation').value,
            contact: document.getElementById('createContact').value,
            deadline: deadline ? deadline.replace('T', ' ') + ':00' : null
        };
        const result = await createTicket(data);
        if (result.success) {
            closeModal('createModal');
            document.getElementById('createForm').reset();
            filters = { status: '', priority: '', group: '', keyword: '' };
            document.getElementById('filterStatus').value = '';
            document.getElementById('filterPriority').value = '';
            document.getElementById('filterGroup').value = '';
            document.getElementById('filterKeyword').value = '';
            if (result.warnings && result.warnings.length) {
                showWarnings(result.warnings);
            }
            await refreshData();
        } else {
            alert('创建失败：' + (result.errors || []).join(', '));
        }
    });

    document.getElementById('assignForm').addEventListener('submit', async e => {
        e.preventDefault();
        const id = document.getElementById('assignTicketId').value;
        const assignee = document.getElementById('assignAssignee').value;
        const result = await assignTicket(id, assignee);
        if (result.success) {
            closeModal('assignModal');
            await refreshData();
        } else {
            alert('指派失败：' + (result.errors || []).join(', '));
        }
    });

    document.getElementById('warningClose').addEventListener('click', () => {
        document.getElementById('warningSection').style.display = 'none';
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await fetchMeta();
    await refreshData();
});
