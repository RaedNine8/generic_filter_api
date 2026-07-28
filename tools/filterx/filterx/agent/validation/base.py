from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FilterValidationError:
    code: str
    message: str
    path: str = ""
    context: dict[str, Any] = field(default_factory=dict)


class Validator(ABC):
    @abstractmethod
    def validate(self, entity_name: str, filter_tree: dict[str, Any]) -> list[FilterValidationError]:
        raise NotImplementedError


class ValidationPipeline:
    def __init__(self, validators: list[Validator]) -> None:
        self.validators = validators

    def validate(self, entity_name: str, filter_tree: dict[str, Any]) -> list[FilterValidationError]:
        errors: list[FilterValidationError] = []
        for validator in self.validators:
            next_errors = validator.validate(entity_name, filter_tree)
            errors.extend(next_errors)
            if any(error.code == "INVALID_SCHEMA_SHAPE" for error in next_errors):
                break
        return errors
