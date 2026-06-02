"""benchmarks 装饰器:每题一个 @bench(...) 函数,返回 build123d Part / Compound。

用法见 models/01_calibration_block.py。

注意:本模块只做注册,不在 import 期实际跑题(避免 import benchmarks 就触发 build123d)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

Suite = Literal["fast", "full"]

_REGISTRY: list["Bench"] = []


@dataclass
class Bench:
    name: str
    suite: tuple[Suite, ...]
    difficulty: int          # 1~5 stars
    timeout_seconds: int
    builder: Callable        # () -> Part | Compound
    extra_outputs: tuple[str, ...] = field(default_factory=tuple)


def bench(
    name: str,
    *,
    suite: tuple[Suite, ...] = ("full",),
    difficulty: int = 1,
    timeout_seconds: int = 60,
    extra_outputs: tuple[str, ...] = (),
):
    """装饰器:把一个 build123d builder 函数注册成 benchmark case。"""
    def decorator(fn: Callable) -> Callable:
        _REGISTRY.append(
            Bench(
                name=name,
                suite=suite,
                difficulty=difficulty,
                timeout_seconds=timeout_seconds,
                builder=fn,
                extra_outputs=tuple(extra_outputs),
            )
        )
        return fn
    return decorator


def all_benches() -> list[Bench]:
    return list(_REGISTRY)


def filter_suite(s: Suite) -> list[Bench]:
    return [b for b in _REGISTRY if s in b.suite]
