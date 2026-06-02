from datetime import datetime
import sys
import os
import difflib

sys.path.insert(0, os.path.dirname(__file__))
from models import (Ticket, load_tickets, save_tickets, STATUS_OPTIONS,
                    PRIORITY_OPTIONS, GROUP_OPTIONS, VALID_TRANSITIONS,
                    STATUS_LABELS, GROUP_LABELS)

PENDING_STATUSES = ['new', 'assigned', 'in_progress', 'blocked']


def generate_ticket_id():
    now = datetime.now()
    date_str = now.strftime('%Y%m%d')
    tickets = load_tickets()
    today_tickets = [t for t in tickets if t.id.startswith(f'TK-{date_str}-')]
    next_num = len(today_tickets) + 1
    return f'TK-{date_str}-{next_num:03d}'


def get_ticket_list(status=None, priority=None, group=None, keyword=None):
    tickets = load_tickets()
    if status:
        status_lower = status.lower()
        tickets = [t for t in tickets if t.status.lower() == status_lower]
    if priority:
        priority_lower = priority.lower()
        tickets = [t for t in tickets if t.priority.lower() == priority_lower]
    if group:
        group_lower = group.lower()
        tickets = [t for t in tickets if t.group.lower() == group_lower]
    if keyword:
        kw = keyword.lower().strip()
        if kw:
            tickets = [t for t in tickets if
                       kw in t.title.lower() or
                       kw in t.location.lower() or
                       kw in t.assignee.lower() or
                       kw in t.contact.lower()]
    tickets.sort(key=lambda t: t.updated_at, reverse=True)
    return [t.to_dict() for t in tickets]


def get_ticket_by_id(ticket_id):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            return ticket.to_dict()
    return None


def check_duplicate(title, location, contact):
    tickets = load_tickets()
    open_tickets = [t for t in tickets if t.status.lower() not in ('resolved', 'closed')]
    warnings = []
    for t in open_tickets:
        title_sim = difflib.SequenceMatcher(None, title.lower(), t.title.lower()).ratio()
        if (title_sim > 0.7 and
                t.location.lower() == location.lower() and
                t.contact.lower() == contact.lower()):
            warnings.append({
                'id': t.id,
                'title': t.title,
                'similarity': round(title_sim, 2)
            })
    return warnings


def create_ticket(title, priority, group, assignee='', location='',
                  contact='', deadline=None, operator='system'):
    status = 'new'
    if assignee:
        status = 'assigned'
    ticket = Ticket(
        id=generate_ticket_id(),
        title=title,
        status=status,
        priority=priority.lower(),
        assignee=assignee,
        group=group.lower(),
        location=location,
        contact=contact,
        deadline=deadline,
        audit_log=[]
    )
    errors = ticket.validate()
    if errors:
        return {'success': False, 'errors': errors}
    action = 'assigned' if status == 'assigned' else 'created'
    ticket.add_audit_entry(action, f'status={status}, title={title}', operator)
    tickets = load_tickets()
    tickets.append(ticket)
    save_tickets(tickets)
    warnings = check_duplicate(title, location, contact)
    result = {'success': True, 'ticket': ticket.to_dict()}
    if warnings:
        result['warnings'] = warnings
    return result


def update_ticket_status(ticket_id, new_status, operator='system'):
    new_status_lower = new_status.lower() if new_status else ''
    if new_status_lower not in STATUS_OPTIONS:
        return {'success': False, 'errors': [f'status must be one of {STATUS_OPTIONS}']}
    tickets = load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            current = ticket.status.lower()
            if new_status_lower not in VALID_TRANSITIONS.get(current, []):
                return {
                    'success': False,
                    'errors': [f'cannot transition from {current} to {new_status_lower}',
                               f'allowed: {VALID_TRANSITIONS.get(current, [])}']
                }
            ticket.status = new_status_lower
            ticket.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ticket.add_audit_entry('status_change',
                                   f'{current} -> {new_status_lower}', operator)
            save_tickets(tickets)
            return {'success': True, 'ticket': ticket.to_dict()}
    return {'success': False, 'errors': ['ticket not found']}


def assign_ticket(ticket_id, assignee, operator='system'):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket.id == ticket_id:
            old_assignee = ticket.assignee
            ticket.assignee = assignee
            ticket.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if ticket.status.lower() == 'new':
                ticket.status = 'assigned'
                ticket.add_audit_entry('assign',
                                       f'assigned to {assignee}, status new->assigned',
                                       operator)
            else:
                ticket.add_audit_entry('assign',
                                       f'reassigned from {old_assignee} to {assignee}',
                                       operator)
            save_tickets(tickets)
            return {'success': True, 'ticket': ticket.to_dict()}
    return {'success': False, 'errors': ['ticket not found']}


def get_status_statistics():
    tickets = load_tickets()
    stats = {status: 0 for status in STATUS_OPTIONS}
    for ticket in tickets:
        sl = ticket.status.lower()
        if sl in stats:
            stats[sl] += 1
    total = len(tickets)
    stats['total'] = total
    pending_count = sum(stats.get(s, 0) for s in PENDING_STATUSES)
    stats['pending_total'] = pending_count
    return stats


def get_group_statistics():
    tickets = load_tickets()
    group_stats = {}
    for g in GROUP_OPTIONS:
        open_for_group = [t for t in tickets
                          if t.group.lower() == g and t.status.lower() in PENDING_STATUSES]
        group_stats[g] = len(open_for_group)
    return group_stats


def get_overdue_statistics():
    tickets = load_tickets()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    now_dt = datetime.now()
    overdue = 0
    near_overdue = 0
    for ticket in tickets:
        if ticket.status.lower() in PENDING_STATUSES and ticket.deadline:
            try:
                deadline_dt = datetime.strptime(ticket.deadline, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    deadline_dt = datetime.strptime(ticket.deadline, '%Y-%m-%d')
                except ValueError:
                    continue
            diff = (deadline_dt - now_dt).total_seconds()
            if diff < 0:
                overdue += 1
            elif diff < 86400:
                near_overdue += 1
    return {'overdue': overdue, 'near_overdue': near_overdue}


def get_full_statistics():
    status_stats = get_status_statistics()
    group_stats = get_group_statistics()
    overdue_stats = get_overdue_statistics()
    status_stats['by_group'] = group_stats
    status_stats['overdue'] = overdue_stats['overdue']
    status_stats['near_overdue'] = overdue_stats['near_overdue']
    return status_stats
