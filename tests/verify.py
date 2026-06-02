import sys
import os
import json
import shutil
from datetime import datetime, timedelta

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import (Ticket, load_tickets, save_tickets, STATUS_OPTIONS,
                    PRIORITY_OPTIONS, GROUP_OPTIONS, VALID_TRANSITIONS,
                    DATA_FILE)
import services

BACKUP_FILE = DATA_FILE + '.bak'

ORIGINAL_DATA = None


def backup_data():
    global ORIGINAL_DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            ORIGINAL_DATA = f.read()
        shutil.copy2(DATA_FILE, BACKUP_FILE)


def restore_data():
    global ORIGINAL_DATA
    if ORIGINAL_DATA is not None:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(ORIGINAL_DATA)
        if os.path.exists(BACKUP_FILE):
            os.remove(BACKUP_FILE)
    elif os.path.exists(BACKUP_FILE):
        shutil.move(BACKUP_FILE, DATA_FILE)


def write_test_data(tickets_data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(tickets_data, f, ensure_ascii=False, indent=2)


def setup_basic_data():
    write_test_data([
        {
            "id": "VT-001", "title": "test ticket one", "status": "new",
            "priority": "high", "assignee": "", "group": "dormitory",
            "location": "5-301", "contact": "13800001111", "deadline": None,
            "audit_log": [{"time": "2026-06-01 09:00:00", "action": "created", "detail": "status=new", "operator": "system"}],
            "updated_at": "2026-06-01 09:00:00"
        },
        {
            "id": "VT-002", "title": "test ticket two", "status": "assigned",
            "priority": "medium", "assignee": "Zhang", "group": "it_center",
            "location": "Lib-201", "contact": "13900002222", "deadline": None,
            "audit_log": [{"time": "2026-06-01 10:00:00", "action": "created", "detail": "status=new", "operator": "system"}],
            "updated_at": "2026-06-01 10:00:00"
        },
        {
            "id": "VT-003", "title": "test ticket three", "status": "in_progress",
            "priority": "low", "assignee": "Wang", "group": "logistics",
            "location": "Canteen-1", "contact": "13700003333", "deadline": None,
            "audit_log": [], "updated_at": "2026-06-01 11:00:00"
        },
        {
            "id": "VT-004", "title": "test ticket four", "status": "resolved",
            "priority": "medium", "assignee": "Li", "group": "it_center",
            "location": "Admin-101", "contact": "13600004444", "deadline": None,
            "audit_log": [], "updated_at": "2026-06-01 12:00:00"
        }
    ])


def run_test(name, test_func):
    try:
        result = test_func()
        if result:
            print(f"[PASS] {name}")
            return True
        else:
            print(f"[FAIL] {name}")
            return False
    except Exception as e:
        print(f"[ERROR] {name}: {str(e)}")
        return False


def test_ticket_model_new_fields():
    ticket = Ticket(
        id="M-001", title="model test", status="new", priority="high",
        assignee="", group="dormitory", location="B5-3F", contact="111",
        deadline="2026-06-10 18:00:00"
    )
    d = ticket.to_dict()
    return (d['group'] == 'dormitory' and
            d['location'] == 'B5-3F' and
            d['contact'] == '111' and
            d['deadline'] == '2026-06-10 18:00:00' and
            d['audit_log'] == [])


def test_ticket_from_dict_new_fields():
    data = {
        "id": "M-002", "title": "from dict", "status": "assigned",
        "priority": "medium", "assignee": "Tester", "group": "it_center",
        "location": "Lab", "contact": "222", "deadline": "2026-07-01",
        "audit_log": [{"time": "2026-06-01 08:00:00", "action": "created", "detail": "x", "operator": "sys"}],
        "updated_at": "2026-06-01 08:00:00"
    }
    t = Ticket.from_dict(data)
    return (t.group == 'it_center' and
            t.location == 'Lab' and
            t.contact == '222' and
            t.deadline == '2026-07-01' and
            len(t.audit_log) == 1)


def test_ticket_validate():
    t1 = Ticket(id="V-01", title="ok", status="new", priority="high", assignee="", group="dormitory")
    t2 = Ticket(id="", title="", status="bad", priority="bad", assignee="", group="bad")
    return len(t1.validate()) == 0 and len(t2.validate()) >= 4


def test_audit_log_entry():
    t = Ticket(id="A-01", title="audit", status="new", priority="high", assignee="", group="logistics")
    t.add_audit_entry('status_change', 'new -> assigned', 'admin')
    return (len(t.audit_log) == 1 and
            t.audit_log[0]['action'] == 'status_change' and
            t.audit_log[0]['detail'] == 'new -> assigned' and
            t.audit_log[0]['operator'] == 'admin')


def test_valid_transitions_closed_cannot_reopen():
    return VALID_TRANSITIONS.get('closed', []) == []


def test_valid_transitions_new_allowed():
    allowed = VALID_TRANSITIONS.get('new', [])
    return 'assigned' in allowed and 'closed' in allowed and 'in_progress' not in allowed


def test_valid_transitions_resolved_only_closed():
    return VALID_TRANSITIONS.get('resolved', []) == ['closed']


def test_create_ticket_default_new():
    setup_basic_data()
    result = services.create_ticket(title="new one", priority="high", group="dormitory")
    return (result['success'] and
            result['ticket']['status'] == 'new' and
            result['ticket']['group'] == 'dormitory')


def test_create_ticket_with_assignee_auto_assigned():
    setup_basic_data()
    result = services.create_ticket(title="assigned one", priority="medium", group="it_center", assignee="Zhang")
    return (result['success'] and
            result['ticket']['status'] == 'assigned' and
            result['ticket']['assignee'] == 'Zhang')


def test_create_ticket_audit_log_written():
    setup_basic_data()
    result = services.create_ticket(title="audit test", priority="low", group="logistics")
    if not result['success']:
        return False
    log = result['ticket']['audit_log']
    return len(log) >= 1 and log[0]['action'] == 'created'


def test_create_ticket_with_assignee_audit():
    setup_basic_data()
    result = services.create_ticket(title="auto assign", priority="medium", group="dormitory", assignee="Li")
    if not result['success']:
        return False
    log = result['ticket']['audit_log']
    return len(log) >= 1 and log[0]['action'] == 'assigned'


def test_create_ticket_validation_error():
    setup_basic_data()
    result = services.create_ticket(title="", priority="invalid", group="bad_group")
    return not result['success'] and len(result['errors']) >= 2


def test_duplicate_detection():
    setup_basic_data()
    result = services.create_ticket(
        title="test ticket one!!!",
        priority="high", group="dormitory",
        location="5-301", contact="13800001111"
    )
    if not result['success']:
        return False
    return 'warnings' in result and len(result['warnings']) > 0


def test_duplicate_not_triggered_for_different_location():
    setup_basic_data()
    result = services.create_ticket(
        title="test ticket one",
        priority="high", group="dormitory",
        location="DIFFERENT-LOC", contact="13800001111"
    )
    return result['success'] and 'warnings' not in result


def test_duplicate_not_triggered_for_resolved():
    setup_basic_data()
    result = services.create_ticket(
        title="test ticket four",
        priority="medium", group="it_center",
        location="Admin-101", contact="13600004444"
    )
    return result['success'] and 'warnings' not in result


def test_status_transition_valid():
    setup_basic_data()
    result = services.update_ticket_status('VT-001', 'assigned')
    return (result['success'] and
            result['ticket']['status'] == 'assigned')


def test_status_transition_audit_written():
    setup_basic_data()
    result = services.update_ticket_status('VT-001', 'assigned')
    if not result['success']:
        return False
    log = result['ticket']['audit_log']
    return len(log) >= 2 and log[-1]['action'] == 'status_change'


def test_status_transition_invalid_closed_to_new():
    setup_basic_data()
    write_test_data([
        {"id": "CL-001", "title": "closed one", "status": "closed", "priority": "low",
         "assignee": "X", "group": "dormitory", "location": "", "contact": "",
         "deadline": None, "audit_log": [], "updated_at": "2026-06-01 09:00:00"}
    ])
    result = services.update_ticket_status('CL-001', 'new')
    return not result['success']


def test_status_transition_invalid_resolved_to_new():
    setup_basic_data()
    result = services.update_ticket_status('VT-004', 'new')
    return not result['success']


def test_status_transition_invalid_skip():
    setup_basic_data()
    result = services.update_ticket_status('VT-001', 'in_progress')
    return not result['success']


def test_assign_ticket():
    setup_basic_data()
    result = services.assign_ticket('VT-001', 'NewPerson')
    return (result['success'] and
            result['ticket']['assignee'] == 'NewPerson' and
            result['ticket']['status'] == 'assigned')


def test_assign_new_ticket_auto_status():
    setup_basic_data()
    result = services.assign_ticket('VT-001', 'NewPerson')
    return result['success'] and result['ticket']['status'] == 'assigned'


def test_assign_audit_written():
    setup_basic_data()
    result = services.assign_ticket('VT-001', 'NewPerson')
    if not result['success']:
        return False
    log = result['ticket']['audit_log']
    return len(log) >= 2 and log[-1]['action'] == 'assign'


def test_filter_by_status():
    setup_basic_data()
    result = services.get_ticket_list(status='new')
    return len(result) == 1 and result[0]['status'] == 'new'


def test_filter_by_priority():
    setup_basic_data()
    result = services.get_ticket_list(priority='high')
    return len(result) == 1 and result[0]['priority'] == 'high'


def test_filter_by_group():
    setup_basic_data()
    result = services.get_ticket_list(group='it_center')
    return len(result) == 2 and all(t['group'] == 'it_center' for t in result)


def test_filter_by_keyword():
    setup_basic_data()
    result = services.get_ticket_list(keyword='one')
    return len(result) == 1 and 'one' in result[0]['title']


def test_combined_filters():
    setup_basic_data()
    result = services.get_ticket_list(status='assigned', group='it_center')
    return len(result) == 1 and result[0]['id'] == 'VT-002'


def test_combined_filters_no_result():
    setup_basic_data()
    result = services.get_ticket_list(status='new', group='it_center')
    return len(result) == 0


def test_filter_empty_values():
    setup_basic_data()
    result = services.get_ticket_list(status='', priority='', group='', keyword='')
    return len(result) == 4


def test_filter_case_insensitive():
    setup_basic_data()
    r1 = services.get_ticket_list(status='NEW')
    r2 = services.get_ticket_list(group='IT_CENTER')
    return len(r1) == 1 and len(r2) == 2


def test_stats_basic():
    setup_basic_data()
    stats = services.get_full_statistics()
    return (stats['total'] == 4 and
            stats['pending_total'] == 3 and
            stats.get('new', 0) == 1 and
            stats.get('assigned', 0) == 1 and
            stats.get('in_progress', 0) == 1)


def test_stats_resolved_closed_not_in_pending():
    setup_basic_data()
    stats = services.get_full_statistics()
    return stats['pending_total'] == stats.get('new', 0) + stats.get('assigned', 0) + stats.get('in_progress', 0) + stats.get('blocked', 0)


def test_stats_by_group():
    setup_basic_data()
    stats = services.get_full_statistics()
    bg = stats.get('by_group', {})
    return bg.get('dormitory', 0) == 1 and bg.get('it_center', 0) == 1 and bg.get('logistics', 0) == 1


def test_overdue_statistics():
    past = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
    write_test_data([
        {"id": "OD-001", "title": "overdue ticket", "status": "in_progress",
         "priority": "high", "assignee": "X", "group": "dormitory",
         "location": "", "contact": "", "deadline": past,
         "audit_log": [], "updated_at": "2026-06-01 09:00:00"}
    ])
    stats = services.get_overdue_statistics()
    return stats['overdue'] >= 1


def test_near_overdue_statistics():
    near = (datetime.now() + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
    write_test_data([
        {"id": "ND-001", "title": "near overdue ticket", "status": "in_progress",
         "priority": "high", "assignee": "X", "group": "it_center",
         "location": "", "contact": "", "deadline": near,
         "audit_log": [], "updated_at": "2026-06-01 09:00:00"}
    ])
    stats = services.get_overdue_statistics()
    return stats['near_overdue'] >= 1


def test_overdue_excludes_resolved():
    past = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
    write_test_data([
        {"id": "ROD-001", "title": "resolved overdue", "status": "resolved",
         "priority": "high", "assignee": "X", "group": "logistics",
         "location": "", "contact": "", "deadline": past,
         "audit_log": [], "updated_at": "2026-06-01 09:00:00"}
    ])
    stats = services.get_overdue_statistics()
    return stats['overdue'] == 0


def test_full_statistics_includes_all():
    setup_basic_data()
    stats = services.get_full_statistics()
    return ('total' in stats and
            'pending_total' in stats and
            'by_group' in stats and
            'overdue' in stats and
            'near_overdue' in stats)


def test_data_persistence():
    setup_basic_data()
    services.update_ticket_status('VT-001', 'assigned')
    ticket = services.get_ticket_by_id('VT-001')
    return ticket['status'] == 'assigned'


def test_assign_not_found():
    setup_basic_data()
    result = services.assign_ticket('NONEXISTENT', 'Someone')
    return not result['success']


def test_status_change_not_found():
    setup_basic_data()
    result = services.update_ticket_status('NONEXISTENT', 'assigned')
    return not result['success']


def main():
    print("=" * 60)
    print("Campus Ops Lite - Verification Script")
    print("=" * 60)
    print()

    backup_data()
    setup_basic_data()

    tests = [
        ("Ticket model - new fields", test_ticket_model_new_fields),
        ("Ticket from_dict - new fields", test_ticket_from_dict_new_fields),
        ("Ticket validation", test_ticket_validate),
        ("Audit log entry", test_audit_log_entry),
        ("Transitions - closed cannot reopen", test_valid_transitions_closed_cannot_reopen),
        ("Transitions - new allowed paths", test_valid_transitions_new_allowed),
        ("Transitions - resolved only to closed", test_valid_transitions_resolved_only_closed),
        ("Create ticket - default new", test_create_ticket_default_new),
        ("Create ticket - with assignee auto assigned", test_create_ticket_with_assignee_auto_assigned),
        ("Create ticket - audit log written", test_create_ticket_audit_log_written),
        ("Create ticket - assignee audit", test_create_ticket_with_assignee_audit),
        ("Create ticket - validation error", test_create_ticket_validation_error),
        ("Duplicate - detected for similar", test_duplicate_detection),
        ("Duplicate - not triggered different location", test_duplicate_not_triggered_for_different_location),
        ("Duplicate - not triggered for resolved", test_duplicate_not_triggered_for_resolved),
        ("Status transition - valid", test_status_transition_valid),
        ("Status transition - audit written", test_status_transition_audit_written),
        ("Status transition - closed to new blocked", test_status_transition_invalid_closed_to_new),
        ("Status transition - resolved to new blocked", test_status_transition_invalid_resolved_to_new),
        ("Status transition - skip step blocked", test_status_transition_invalid_skip),
        ("Assign ticket", test_assign_ticket),
        ("Assign new ticket - auto status", test_assign_new_ticket_auto_status),
        ("Assign - audit written", test_assign_audit_written),
        ("Filter - by status", test_filter_by_status),
        ("Filter - by priority", test_filter_by_priority),
        ("Filter - by group", test_filter_by_group),
        ("Filter - by keyword", test_filter_by_keyword),
        ("Filter - combined status+group", test_combined_filters),
        ("Filter - combined no result", test_combined_filters_no_result),
        ("Filter - empty values", test_filter_empty_values),
        ("Filter - case insensitive", test_filter_case_insensitive),
        ("Stats - basic counts", test_stats_basic),
        ("Stats - resolved/closed not in pending", test_stats_resolved_closed_not_in_pending),
        ("Stats - by group pending", test_stats_by_group),
        ("Overdue - detection", test_overdue_statistics),
        ("Near overdue - detection", test_near_overdue_statistics),
        ("Overdue - excludes resolved", test_overdue_excludes_resolved),
        ("Full statistics - all fields", test_full_statistics_includes_all),
        ("Data persistence", test_data_persistence),
        ("Assign not found", test_assign_not_found),
        ("Status change not found", test_status_change_not_found),
    ]

    passed = 0
    failed = 0

    print("Running test cases...")
    print("-" * 60)

    for name, test_func in tests:
        if run_test(name, test_func):
            passed += 1
        else:
            failed += 1

    print("-" * 60)
    print(f"\nResults: {passed} / {len(tests)} passed, {failed} failed")

    restore_data()

    if failed == 0:
        print("\nAll tests passed! Core data flow verification successful.")
        return 0
    else:
        print(f"\n{failed} test(s) failed. Please check the code.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
