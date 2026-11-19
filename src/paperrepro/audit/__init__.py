"""Paper-versus-code consistency audit."""

from __future__ import annotations

from .config_audit import AUDITABLE, ParamCheck, audit_parameters

__all__ = ["audit_parameters", "ParamCheck", "AUDITABLE"]
