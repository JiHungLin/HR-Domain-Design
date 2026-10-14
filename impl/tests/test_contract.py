"""實作與 api.yaml 一致（P8）：每個操作都有註冊，路徑、方法、x-concept 相同；請求欄位不超出規格。"""
from app import models, stubs
from app.main import app
from app.routers import uc01

SPEC = stubs.spec()


def _ops(paths):
    return {(m, p): o for p, v in paths.items() for m, o in v.items() if m in ("get", "post")}


def test_every_operation_registered_with_same_concept():
    spec_ops, impl_ops = _ops(SPEC["paths"]), _ops(app.openapi()["paths"])
    assert set(spec_ops) == set(impl_ops)
    for k, o in spec_ops.items():
        assert impl_ops[k]["operationId"] == o["operationId"], k
        assert impl_ops[k].get("x-concept") == o.get("x-concept"), k


def test_request_fields_within_spec():
    implemented = {r.operation_id: r for r in uc01.router.routes}
    for (m, p), o in _ops(SPEC["paths"]).items():
        r = implemented.get(o["operationId"])
        if r is None or "requestBody" not in o:
            continue
        spec_fields = set(o["requestBody"]["content"]["application/json"]["schema"]["properties"])
        model = r.body_field.field_info.annotation
        assert set(model.model_fields) <= spec_fields, (o["operationId"], set(model.model_fields) - spec_fields)
