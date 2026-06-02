import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tickets.json')

STATUS_OPTIONS = ['new', 'assigned', 'in_progress', 'blocked', 'resolved', 'closed']
PRIORITY_OPTIONS = ['low', 'medium', 'high']
GROUP_OPTIONS = ['dormitory', 'logistics', 'it_center']

VALID_TRANSITIONS = {
    'new': ['assigned', 'closed'],
    'assigned': ['in_progress', 'blocked', 'closed'],
    'in_progress': ['blocked', 'resolved', 'closed'],
    'blocked': ['in_progress', 'assigned', 'closed'],
    'resolved': ['closed'],
    'closed': []
}

STATUS_LABELS = {
    'new': '新建',
    'assigned': '已指派',
    'in_progress': '处理中',
    'blocked': '阻塞',
    'resolved': '已解决',
    'closed': '已关闭'
}

GROUP_LABELS = {
    'dormitory': '宿舍管理',
    'logistics': '后勤保障',
    'it_center': '信息中心'
}


class Ticket:
    def __init__(self, id, title, status, priority, assignee, group,
                 location='', contact='', deadline=None, audit_log=None,
                 updated_at=None):
        self.id = id
        self.title = title
        self.status = status
        self.priority = priority
        self.assignee = assignee
        self.group = group
        self.location = location
        self.contact = contact
        self.deadline = deadline
        self.audit_log = audit_log if audit_log is not None else []
        self.updated_at = updated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee,
            'group': self.group,
            'location': self.location,
            'contact': self.contact,
            'deadline': self.deadline,
            'audit_log': self.audit_log,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            title=data['title'],
            status=data.get('status', 'new'),
            priority=data.get('priority', 'medium'),
            assignee=data.get('assignee', ''),
            group=data.get('group', 'logistics'),
            location=data.get('location', ''),
            contact=data.get('contact', ''),
            deadline=data.get('deadline'),
            audit_log=data.get('audit_log', []),
            updated_at=data.get('updated_at')
        )

    def validate(self):
        errors = []
        if not self.id:
            errors.append('ID required')
        if not self.title:
            errors.append('title required')
        if self.status.lower() not in STATUS_OPTIONS:
            errors.append(f'status must be one of {STATUS_OPTIONS}')
        if self.priority.lower() not in PRIORITY_OPTIONS:
            errors.append(f'priority must be one of {PRIORITY_OPTIONS}')
        if self.group.lower() not in GROUP_OPTIONS:
            errors.append(f'group must be one of {GROUP_OPTIONS}')
        return errors

    def add_audit_entry(self, action, detail, operator='system'):
        entry = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': action,
            'detail': detail,
            'operator': operator
        }
        self.audit_log.append(entry)


def load_tickets():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Ticket.from_dict(item) for item in data]


def save_tickets(tickets):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([t.to_dict() for t in tickets], f, ensure_ascii=False, indent=2)
