from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class EntityScope:
    available: tuple[str, ...]
    requested: tuple[str, ...]
    excluded: tuple[str, ...]
    selected: tuple[str, ...]
    unknown_requested: tuple[str, ...]
    unknown_excluded: tuple[str, ...]
    requested_and_excluded: tuple[str, ...]

    @property
    def has_errors(self) -> bool:
        return bool(
            self.unknown_requested
            or self.unknown_excluded
            or self.requested_and_excluded
        )

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "available": list(self.available),
            "requested": list(self.requested),
            "excluded": list(self.excluded),
            "selected": list(self.selected),
            "unknown_requested": list(self.unknown_requested),
            "unknown_excluded": list(self.unknown_excluded),
            "requested_and_excluded": list(self.requested_and_excluded),
        }


def _normalized_names(values: Iterable[str] | None) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values or [] if str(value).strip()}))


def resolve_entity_scope(
    available_names: Iterable[str],
    requested_names: Iterable[str] | None = None,
    excluded_names: Iterable[str] | None = None,
) -> EntityScope:
    available = _normalized_names(available_names)
    requested = _normalized_names(requested_names)
    excluded = _normalized_names(excluded_names)

    available_set = set(available)
    requested_set = set(requested)
    excluded_set = set(excluded)
    selected_set = (requested_set or available_set) - excluded_set

    return EntityScope(
        available=available,
        requested=requested,
        excluded=excluded,
        selected=tuple(name for name in available if name in selected_set),
        unknown_requested=tuple(sorted(requested_set - available_set)),
        unknown_excluded=tuple(sorted(excluded_set - available_set)),
        requested_and_excluded=tuple(sorted(requested_set & excluded_set)),
    )


def select_entity_metadata(
    entities: Sequence[T],
    *,
    requested_names: Iterable[str] | None = None,
    excluded_names: Iterable[str] | None = None,
) -> tuple[list[T], EntityScope]:
    names = [
        str(entity.get("model"))
        for entity in entities
        if isinstance(entity, dict) and entity.get("model")
    ]
    scope = resolve_entity_scope(names, requested_names, excluded_names)
    selected_names = set(scope.selected)
    return [
        entity
        for entity in entities
        if isinstance(entity, dict) and entity.get("model") in selected_names
    ], scope