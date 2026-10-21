"""api.yaml 是請求與回應格式的唯一來源（05_mapping D-18）：請求在這裡依 api.yaml 檢查，不另外手寫一份格式。

hire-employee 與 annual-leave-grant 各有一份 api.yaml；每個 operationId 用它所在那份的 components 檢查。
"""
from functools import lru_cache

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from app import config


class RequestInvalid(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors


@lru_cache
def specs() -> tuple[dict, ...]:
    return tuple(yaml.safe_load(p.read_text(encoding="utf-8")) for p in config.API_SPECS)


def spec() -> dict:
    """hire-employee 的 api.yaml（版本、securitySchemes 取自這份）。"""
    return specs()[0]


@lru_cache
def _index() -> dict[str, tuple[str, str, dict, dict]]:
    out = {}
    for doc in specs():
        for p, ops in doc["paths"].items():
            for m, o in ops.items():
                if m in ("get", "post"):
                    out[o["operationId"]] = (m, p, o, doc)
    return out


@lru_cache
def operations() -> dict[str, tuple[str, str, dict]]:
    """operationId → (method, path, operation)。"""
    return {k: v[:3] for k, v in _index().items()}


def paths() -> list[tuple[str, str, dict]]:
    return [(p, m, o) for m, p, o, _ in _index().values()]


@lru_cache
def components() -> dict:
    """OpenAPI 文件用：兩份的 components 合併（同名的以 hire-employee 為準；兩份只差說明文字）。"""
    merged: dict = {}
    for doc in reversed(specs()):
        for kind, items in doc["components"].items():
            merged.setdefault(kind, {}).update(items)
    return merged


def _with_components(op_id: str, schema: dict) -> dict:
    return {**schema, "components": _index()[op_id][3]["components"]}


def _validator(schema: dict) -> Draft202012Validator:
    # 把 #/components/... 解析到 schema 所在的那份 api.yaml
    root = {"components": spec()["components"], **schema}
    return Draft202012Validator(root, format_checker=FormatChecker())


def request_schema(op_id: str) -> dict:
    return _with_components(op_id, operations()[op_id][2]["requestBody"]["content"]["application/json"]["schema"])


def response_schema(op_id: str, status: int) -> dict:
    return _with_components(op_id, operations()[op_id][2]["responses"][str(status)]["content"]["application/json"]["schema"])


def errors(schema: dict, instance) -> list[str]:
    return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}：{e.message}"
            for e in _validator(schema).iter_errors(instance)]


def validate_request(op_id: str, body) -> dict:
    errs = errors(request_schema(op_id), body)
    if errs:
        raise RequestInvalid(errs)
    return body


def openapi_extra(op_id: str) -> dict:
    """路由的 OpenAPI 直接沿用 api.yaml 的請求、回應與 x- 欄位。"""
    op = operations()[op_id][2]
    return {k: v for k, v in op.items() if k in ("requestBody", "responses") or k.startswith("x-")}
