"""api.yaml 是請求與回應格式的唯一來源（05_mapping D-18）：請求在這裡依 api.yaml 檢查，不另外手寫一份格式。"""
from functools import lru_cache

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from app import config


class RequestInvalid(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors


@lru_cache
def spec() -> dict:
    return yaml.safe_load(config.API_SPEC.read_text(encoding="utf-8"))


@lru_cache
def operations() -> dict[str, tuple[str, str, dict]]:
    """operationId → (method, path, operation)。"""
    return {o["operationId"]: (m, p, o) for p, ops in spec()["paths"].items() for m, o in ops.items()
            if m in ("get", "post")}


def _validator(schema: dict) -> Draft202012Validator:
    # 把 #/components/... 解析到 api.yaml 本身
    root = {**schema, "components": spec()["components"]}
    return Draft202012Validator(root, format_checker=FormatChecker())


def request_schema(op_id: str) -> dict:
    return operations()[op_id][2]["requestBody"]["content"]["application/json"]["schema"]


def response_schema(op_id: str, status: int) -> dict:
    return operations()[op_id][2]["responses"][str(status)]["content"]["application/json"]["schema"]


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
