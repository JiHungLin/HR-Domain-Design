"""其他切片的掛勾（app/hooks.py；annual-leave-grant 05_mapping D-04）：在到職的同一交易中執行，失敗時一起回滾。"""
from bson import ObjectId

from app import hooks
from app.errors import Blocked
from tests.test_guards import _hire, _start


def test_start_employment_calls_hook_in_same_transaction(api, org, db):
    seen = []

    def handler(d, s, e):
        assert s is not None and s.in_transaction
        assert d.employments.find_one({"entity_id": e.employment_id, "is_current": True}, session=s) is not None
        seen.append(e)

    hire = _hire(api, org)
    with hooks.registered(hooks.EMPLOYMENT_STARTED, handler):
        body = _start(api, org, hire["hire_id"]).json()
    assert len(seen) == 1
    e = seen[0]
    assert str(e.event_id) == body["event_id"] and str(e.employment_id) == body["employment_id"]
    assert e.tenant_id == org["tenant"] and e.employer_id == org["employer"]


def test_hook_failure_rolls_back_start_employment(api, org, db):
    def handler(d, s, e):
        raise Blocked("R97", "LEAVE_HOOK_FAILED", "特休的處理擋下")

    hire = _hire(api, org)
    with hooks.registered(hooks.EMPLOYMENT_STARTED, handler):
        r = _start(api, org, hire["hire_id"])
    assert r.status_code == 409 and r.json()["message_code"] == "LEAVE_HOOK_FAILED"
    hid = ObjectId(hire["hire_id"])
    assert db.hires.find_one({"$or": [{"_id": hid}, {"entity_id": hid}], "status": "Started"}) is None
    assert db.employments.count_documents({"hire_id": hid}) == 0
    assert db.events.count_documents({"type": "StartEmployment", "subject.id": hid}) == 0
    # 掛勾移除後同一筆錄用可以正常到職
    assert _start(api, org, hire["hire_id"]).status_code == 201


def test_no_handler_is_noop(api, org):
    hire = _hire(api, org)
    assert _start(api, org, hire["hire_id"]).status_code == 201
