from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from models import Ticket, load_tickets, save_tickets, STATUS_OPTIONS


def generate_ticket_id():
    now = datetime.now()
    date_str = now.strftime('%Y%m%d')
    tickets = load_tickets()
    today_tickets = [t for t in tickets if t.id.startswith(f'TK-{date_str}-')]
    next_num = len(today_tickets) + 1
    return f'TK-{date_str}-{next_num:03d}'


def get_ticket_list(status=None, priority=None):
    tickets = load_tickets()
    if status:
        tickets = [t for t in tickets if t.status == status]
    if priority:
        tickets = [t for t in tickets if t.priority == priority]
    tickets.sort(key=lambda t: t.updated_at, reverse=True)
    return [t.to_dict() for t in tickets]


def get_ticket_by_id(ticket_id):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            return ticket.to_dict()
    return None


def create_ticket(title, priority, assignee):
    ticket = Ticket(
        id=generate_ticket_id(),
        title=title,
        status='pending',
        priority=priority,
        assignee=assignee
    )
    errors = ticket.validate()
    if errors:
        return {'success': False, 'errors': errors}
    tickets = load_tickets()
    tickets.append(ticket)
    save_tickets(tickets)
    return {'success': True, 'ticket': ticket.to_dict()}


def update_ticket_status(ticket_id, new_status):
    if new_status not in STATUS_OPTIONS:
        return {'success': False, 'errors': [f'状态必须是 {STATUS_OPTIONS} 之一']}
    tickets = load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            ticket.status = new_status
            ticket.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_tickets(tickets)
            return {'success': True, 'ticket': ticket.to_dict()}
    return {'success': False, 'errors': ['工单不存在']}


def get_status_statistics():
    tickets = load_tickets()
    stats = {status: 0 for status in STATUS_OPTIONS}
    for ticket in tickets:
        stats[ticket.status] += 1
    total = len(tickets)
    stats['total'] = total
    return stats


def get_priority_statistics():
    tickets = load_tickets()
    stats = {'low': 0, 'medium': 0, 'high': 0}
    for ticket in tickets:
        stats[ticket.priority] += 1
    return stats
