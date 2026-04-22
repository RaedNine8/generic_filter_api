from __future__ import annotations

from .entities import ENTITIES


def build_metadata() -> dict[str, object]:
    return {
        "entities": ENTITIES,
        "entity_count": len(ENTITIES),
    }
