import sys
import os
import json
import shutil
from datetime import datetime

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import Ticket, load_tickets, save_tickets, STATUS_OPTIONS, PRIORITY_OPTIONS, DATA_FILE
import services

BACKUP_FILE = DATA_FILE + '.bak'
TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), 'test_tickets.json')

def backup_data():
    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, BACKUP_FILE)

def restore_data():
    if os.path.exists(BACKUP_FILE):
        shutil.move(BACKUP_FILE, DATA_FILE)

def setup_test_data():
    test_data = [
        {
            "id": "TEST-001",
            "title": "测试工单1",
            "status": "pending",
            "priority": "high",
            "assignee": "测试员A",
            "updated_at": "2026-06-01 10:00:00"
        },
        {
            "id": "TEST-002",
            "title": "测试工单2",
            "status": "processing",
            "priority": "medium",
            "assignee": "测试员B",
            "updated_at": "2026-06-01 11:00:00"
        }
    ]
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

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

def test_ticket_model_creation():
    ticket = Ticket(
        id="TK-TEST",
        title="测试工单",
        status="pending",
        priority="high",
        assignee="测试员"
    )
    return (ticket.id == "TK-TEST" and
            ticket.title == "测试工单" and
            ticket.status == "pending" and
            ticket.priority == "high" and
            ticket.assignee == "测试员" and
            ticket.updated_at is not None)

def test_ticket_validation_valid():
    ticket = Ticket(
        id="TK-TEST",
        title="有效工单",
        status="pending",
        priority="high",
        assignee="测试员"
    )
    errors = ticket.validate()
    return len(errors) == 0

def test_ticket_validation_invalid():
    ticket = Ticket(
        id="",
        title="",
        status="invalid_status",
        priority="invalid_priority",
        assignee=""
    )
    errors = ticket.validate()
    return len(errors) >= 4

def test_ticket_to_dict():
    ticket = Ticket(
        id="TK-TEST",
        title="测试",
        status="pending",
        priority="high",
        assignee="测试员",
        updated_at="2026-06-01 10:00:00"
    )
    data = ticket.to_dict()
    return (data['id'] == 'TK-TEST' and
            data['title'] == '测试' and
            data['status'] == 'pending' and
            data['priority'] == 'high' and
            data['assignee'] == '测试员' and
            data['updated_at'] == '2026-06-01 10:00:00')

def test_ticket_from_dict():
    data = {
        "id": "TK-DICT",
        "title": "从字典创建",
        "status": "processing",
        "priority": "medium",
        "assignee": "测试员",
        "updated_at": "2026-06-01 10:00:00"
    }
    ticket = Ticket.from_dict(data)
    return (ticket.id == "TK-DICT" and
            ticket.title == "从字典创建" and
            ticket.status == "processing")

def test_load_tickets():
    tickets = load_tickets()
    return len(tickets) >= 2 and isinstance(tickets[0], Ticket)

def test_get_ticket_list_all():
    tickets = services.get_ticket_list()
    return len(tickets) >= 2

def test_get_ticket_list_filter_status():
    pending_tickets = services.get_ticket_list(status='pending')
    processing_tickets = services.get_ticket_list(status='processing')
    return (len(pending_tickets) == 1 and
            pending_tickets[0]['status'] == 'pending' and
            len(processing_tickets) == 1 and
            processing_tickets[0]['status'] == 'processing')

def test_get_ticket_by_id():
    ticket = services.get_ticket_by_id('TEST-001')
    return ticket is not None and ticket['id'] == 'TEST-001'

def test_get_ticket_by_id_not_found():
    ticket = services.get_ticket_by_id('NONEXISTENT')
    return ticket is None

def test_get_status_statistics():
    stats = services.get_status_statistics()
    return (stats.get('total') == 2 and
            stats.get('pending') == 1 and
            stats.get('processing') == 1 and
            stats.get('completed') == 0)

def test_generate_ticket_id():
    ticket_id = services.generate_ticket_id()
    today = datetime.now().strftime('%Y%m%d')
    return ticket_id.startswith(f'TK-{today}-')

def test_create_ticket():
    initial_count = len(services.get_ticket_list())
    result = services.create_ticket(
        title="新创建的工单",
        priority="low",
        assignee="新负责人"
    )
    if not result['success']:
        return False
    new_count = len(services.get_ticket_list())
    return (new_count == initial_count + 1 and
            result['ticket']['title'] == '新创建的工单' and
            result['ticket']['status'] == 'pending')

def test_create_ticket_validation_error():
    result = services.create_ticket(
        title="",
        priority="invalid",
        assignee=""
    )
    return not result['success'] and len(result['errors']) > 0

def test_update_ticket_status():
    result = services.update_ticket_status('TEST-001', 'processing')
    if not result['success']:
        return False
    ticket = services.get_ticket_by_id('TEST-001')
    return ticket['status'] == 'processing'

def test_update_ticket_status_invalid():
    result = services.update_ticket_status('TEST-001', 'invalid_status')
    return not result['success']

def test_update_ticket_status_not_found():
    result = services.update_ticket_status('NONEXISTENT', 'completed')
    return not result['success']

def test_data_persistence():
    ticket_id = 'TEST-001'
    original = services.get_ticket_by_id(ticket_id)
    services.update_ticket_status(ticket_id, 'completed')
    reloaded = services.get_ticket_by_id(ticket_id)
    return reloaded['status'] == 'completed'

def test_priority_statistics():
    stats = services.get_priority_statistics()
    return stats.get('high') >= 1 and stats.get('medium') >= 1

def setup_mixed_case_test_data():
    test_data = [
        {
            "id": "CASE-001",
            "title": "大写状态工单",
            "status": "PENDING",
            "priority": "HIGH",
            "assignee": "测试员A",
            "updated_at": "2026-06-01 10:00:00"
        },
        {
            "id": "CASE-002",
            "title": "混合大小写工单",
            "status": "Processing",
            "priority": "Medium",
            "assignee": "测试员B",
            "updated_at": "2026-06-01 11:00:00"
        },
        {
            "id": "CASE-003",
            "title": "正常小写工单",
            "status": "completed",
            "priority": "low",
            "assignee": "测试员C",
            "updated_at": "2026-06-01 12:00:00"
        }
    ]
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

def test_status_filter_case_insensitive():
    setup_mixed_case_test_data()
    result_upper = services.get_ticket_list(status='PENDING')
    result_lower = services.get_ticket_list(status='pending')
    result_mixed = services.get_ticket_list(status='Pending')
    return (len(result_upper) == 1 and
            len(result_lower) == 1 and
            len(result_mixed) == 1 and
            result_upper[0]['id'] == 'CASE-001' and
            result_lower[0]['id'] == 'CASE-001' and
            result_mixed[0]['id'] == 'CASE-001')

def test_priority_filter_case_insensitive():
    setup_mixed_case_test_data()
    result_upper = services.get_ticket_list(priority='HIGH')
    result_lower = services.get_ticket_list(priority='high')
    result_mixed = services.get_ticket_list(priority='High')
    return (len(result_upper) == 1 and
            len(result_lower) == 1 and
            len(result_mixed) == 1 and
            result_upper[0]['priority'] == 'HIGH' and
            result_lower[0]['priority'] == 'HIGH' and
            result_mixed[0]['priority'] == 'HIGH')

def test_update_status_case_insensitive():
    setup_mixed_case_test_data()
    result = services.update_ticket_status('CASE-001', 'PROCESSING')
    if not result['success']:
        return False
    ticket = services.get_ticket_by_id('CASE-001')
    return ticket['status'] == 'processing'

def setup_archived_test_data():
    test_data = [
        {
            "id": "ARCH-001",
            "title": "正常待处理工单",
            "status": "pending",
            "priority": "high",
            "assignee": "测试员A",
            "updated_at": "2026-06-01 10:00:00"
        },
        {
            "id": "ARCH-002",
            "title": "已归档工单",
            "status": "archived",
            "priority": "medium",
            "assignee": "测试员B",
            "updated_at": "2026-06-01 11:00:00"
        },
        {
            "id": "ARCH-003",
            "title": "已关闭工单",
            "status": "closed",
            "priority": "low",
            "assignee": "测试员C",
            "updated_at": "2026-06-01 12:00:00"
        },
        {
            "id": "ARCH-004",
            "title": "处理中工单",
            "status": "processing",
            "priority": "medium",
            "assignee": "测试员D",
            "updated_at": "2026-06-01 13:00:00"
        },
        {
            "id": "ARCH-005",
            "title": "已完成工单",
            "status": "completed",
            "priority": "low",
            "assignee": "测试员E",
            "updated_at": "2026-06-01 14:00:00"
        }
    ]
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

def test_stats_exclude_archived_and_closed():
    setup_archived_test_data()
    stats = services.get_status_statistics()
    return (stats.get('total') == 5 and
            stats.get('pending') == 1 and
            stats.get('processing') == 1 and
            stats.get('completed') == 1)

def test_pending_count_excludes_non_pending():
    setup_archived_test_data()
    stats = services.get_status_statistics()
    return stats.get('pending') == 1

def test_create_ticket_updates_pending_count():
    setup_archived_test_data()
    initial_stats = services.get_status_statistics()
    initial_pending = initial_stats.get('pending', 0)

    result = services.create_ticket(
        title="新增测试工单",
        priority="medium",
        assignee="测试员F"
    )
    if not result['success']:
        return False

    new_stats = services.get_status_statistics()
    new_pending = new_stats.get('pending', 0)

    return new_pending == initial_pending + 1

def test_mixed_case_status_statistics():
    setup_mixed_case_test_data()
    stats = services.get_status_statistics()
    return (stats.get('total') == 3 and
            stats.get('pending') == 1 and
            stats.get('processing') == 1 and
            stats.get('completed') == 1)

def main():
    print("=" * 60)
    print("Campus Ops Lite - 核心数据流验证脚本")
    print("=" * 60)
    print()

    backup_data()
    setup_test_data()

    tests = [
        ("Ticket 模型创建", test_ticket_model_creation),
        ("Ticket 验证 - 有效数据", test_ticket_validation_valid),
        ("Ticket 验证 - 无效数据", test_ticket_validation_invalid),
        ("Ticket 转字典", test_ticket_to_dict),
        ("Ticket 从字典创建", test_ticket_from_dict),
        ("加载工单列表", test_load_tickets),
        ("获取全部工单列表", test_get_ticket_list_all),
        ("按状态筛选工单", test_get_ticket_list_filter_status),
        ("按ID获取工单（存在）", test_get_ticket_by_id),
        ("按ID获取工单（不存在）", test_get_ticket_by_id_not_found),
        ("状态统计", test_get_status_statistics),
        ("生成工单编号", test_generate_ticket_id),
        ("创建工单", test_create_ticket),
        ("创建工单 - 验证失败", test_create_ticket_validation_error),
        ("更新工单状态", test_update_ticket_status),
        ("更新工单状态 - 无效状态", test_update_ticket_status_invalid),
        ("更新工单状态 - 不存在", test_update_ticket_status_not_found),
        ("数据持久化", test_data_persistence),
        ("优先级统计", test_priority_statistics),
        ("[回归] 状态筛选大小写不敏感", test_status_filter_case_insensitive),
        ("[回归] 优先级筛选大小写不敏感", test_priority_filter_case_insensitive),
        ("[回归] 更新状态大小写不敏感", test_update_status_case_insensitive),
        ("[回归] 统计排除归档/关闭状态", test_stats_exclude_archived_and_closed),
        ("[回归] 待处理数量排除非pending", test_pending_count_excludes_non_pending),
        ("[回归] 创建工单后pending数增加", test_create_ticket_updates_pending_count),
        ("[回归] 混合大小写状态统计", test_mixed_case_status_statistics),
    ]

    passed = 0
    failed = 0

    print("运行测试用例...")
    print("-" * 60)

    for name, test_func in tests:
        if run_test(name, test_func):
            passed += 1
        else:
            failed += 1

    print("-" * 60)
    print(f"\n测试完成: 通过 {passed} / {len(tests)}, 失败 {failed}")

    restore_data()

    if failed == 0:
        print("\nAll tests passed! Core data flow verification successful.")
        return 0
    else:
        print(f"\n{failed} test(s) failed. Please check the code.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
