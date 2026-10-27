"""模块注册表：每个计算模块以统一契约接入。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ModuleDef:
    key: str
    title: str
    standard: str
    verified: bool
    param_spec: Callable[[], dict[str, Any]]
    run: Callable[[dict[str, Any]], dict[str, Any]]
    geometry: Callable[[dict[str, Any], str], dict[str, Any]]
    report: Callable[
        [dict[str, Any], dict[str, Any], dict[str, str] | None],
        bytes,
    ]
    category: str = "脚手架"


_REGISTRY: dict[str, ModuleDef] = {}


def register(module: ModuleDef) -> ModuleDef:
    _REGISTRY[module.key] = module
    return module


def get(key: str) -> ModuleDef | None:
    return _REGISTRY.get(key)


def require(key: str) -> ModuleDef:
    module = _REGISTRY.get(key)
    if module is None:
        raise KeyError(key)
    return module


def list_modules() -> list[dict[str, Any]]:
    return [
        {
            "key": m.key,
            "title": m.title,
            "standard": m.standard,
            "verified": m.verified,
            "category": m.category,
        }
        for m in _REGISTRY.values()
    ]
