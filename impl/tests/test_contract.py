"""實作與 api.yaml 一致（P8、05_mapping D-18）：每個操作都有註冊，請求、回應格式與 x- 欄位直接取自 api.yaml。

回應內容是否符合格式，由 tests/conftest.py 的 Api 在每次呼叫時檢查。
"""
from app import spec
from app.main import app


def _ops(paths):
    return {(m, p): o for p, v in paths.items() for m, o in v.items() if m in ("get", "post")}


def test_every_operation_matches_spec():
    spec_ops, impl_ops = _ops(spec.spec()["paths"]), _ops(app.openapi()["paths"])
    assert set(spec_ops) == set(impl_ops)
    for k, o in spec_ops.items():
        impl = impl_ops[k]
        assert impl["operationId"] == o["operationId"], k
        for field in ("requestBody", "responses"):
            assert impl.get(field) == o.get(field), (k, field)
        for x in (f for f in o if f.startswith("x-")):
            assert impl.get(x) == o[x], (k, x)
        spec_params = {p["name"] for p in o.get("parameters", [])}
        impl_params = {p["name"] for p in impl.get("parameters", [])}
        assert spec_params == impl_params, (k, spec_params, impl_params)


def test_components_from_spec():
    assert app.openapi()["components"] == spec.spec()["components"]


def test_request_rejected_when_not_in_spec(api, org):
    # additionalProperties: false；必填缺少
    r = api("decideHire", org["hr"], json={"employer_id": str(org["employer"]), "decided_on": "2026-02-16",
                                           "planned_start_date": "2026-03-02", "person": {"person": {"legal_name": "x"}},
                                           "unexpected": 1})
    assert r.status_code == 422
    r = api("startEmployment", org["hr"], path={"id": "0" * 24}, json={"start_date": "2026-03-02"})
    assert r.status_code == 422          # work_location_id 必填
