from __future__ import annotations

from typing import Callable, Iterable


PredicateHook = Callable[[str, object], object]


def register_global_predicates(hooks: Iterable[PredicateHook]) -> list[PredicateHook]:
    return [hook for hook in hooks]
