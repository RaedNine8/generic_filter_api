from __future__ import annotations

from typing import Any

from .base import RendererTarget


class FastAPISQLAlchemyRenderer:
    name = "fastapi-sqlalchemy"
    version = "1.0.0"
    target = RendererTarget.BACKEND

    def install(self, args: Any) -> int:
        from filterx.commands.backend import _run_fastapi_sqlalchemy_install

        return _run_fastapi_sqlalchemy_install(args)

    def validate(self, args: Any) -> int:
        from filterx.commands.backend import _run_fastapi_sqlalchemy_validate

        return _run_fastapi_sqlalchemy_validate(args)

    def remove(self, args: Any) -> int:
        from filterx.commands.backend import _run_fastapi_sqlalchemy_remove

        return _run_fastapi_sqlalchemy_remove(args)


class AngularRenderer:
    name = "angular"
    version = "1.0.0"
    target = RendererTarget.FRONTEND

    def install(self, args: Any) -> int:
        from filterx.commands.frontend import _run_angular_install

        return _run_angular_install(args)

    def validate(self, args: Any) -> int:
        from filterx.commands.frontend import _run_angular_validate

        return _run_angular_validate(args)

    def remove(self, args: Any) -> int:
        from filterx.commands.frontend import _run_angular_remove

        return _run_angular_remove(args)
