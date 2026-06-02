import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tickets.json')

STATUS_OPTIONS = ['pending', 'processing', 'completed']
PRIORITY_OPTIONS = ['low', 'medium', 'high']


class Ticket:
    def __init__(self, id, title, status, priority, assignee, updated_at=None):
        self.id = id
        self.title = title
        self.status = status
        self.priority = priority
        self.assignee = assignee
        self.updated_at = updated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            title=data['title'],
            status=data['status'],
            priority=data['priority'],
            assignee=data['assignee'],
            updated_at=data.get('updated_at')
        )

    def validate(self):
        errors = []
        if not self.id:
            errors.append('工单编号不能为空')
        if not self.title:
            errors.append('工单标题不能为空')
        if self.status not in STATUS_OPTIONS:
            errors.append(f'状态必须是 {STATUS_OPTIONS} 之一')
        if self.priority not in PRIORITY_OPTIONS:
            errors.append(f'优先级必须是 {PRIORITY_OPTIONS} 之一')
        if not self.assignee:
            errors.append('负责人不能为空')
        return errors


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
