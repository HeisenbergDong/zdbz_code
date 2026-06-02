import sys
import os
import json
import shutil
from datetime import datetime

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
            print(f"✅ {name}: PASS")
            return True
        else:
            print(f"❌ {name}: FAIL")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
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
        print("\n🎉 所有测试通过！核心数据流验证成功。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查代码。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
