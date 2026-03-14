# packages/core/src/zorivest_core/domain/step_registry.py
"""Step type registry for the pipeline engine (Phase 9).

Implements:
- STEP_REGISTRY: module-level dict of registered step types
- RegisteredStep: base class with __init_subclass__ auto-registration
- get_step, has_step, list_steps, get_all_steps helper functions

Spec references: 09-scheduling.md §9.1e, §9.1f
"""

from __future__ import annotations

from typing import Any, ClassVar, Protocol, runtime_checkable

from zorivest_core.domain.pipeline import StepContext, StepResult


# ---------------------------------------------------------------------------
# §9.1e: StepBase Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class StepBase(Protocol):
    """Protocol that all pipeline step types must implement.

    Step types self-register via __init_subclass__. Each step declares:
    - type_name: unique identifier used in policy JSON
    - side_effects: whether the step mutates external state (email, DB write)
    - Params: Pydantic model for parameter validation
    """

    type_name: ClassVar[str]
    side_effects: ClassVar[bool]

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the step with resolved parameters and shared context."""
        ...

    @classmethod
    def params_schema(cls) -> dict:
        """Return JSON Schema for this step's parameters (from Pydantic model)."""
        ...

    async def compensate(
        self, params: dict, context: StepContext, prior_result: StepResult
    ) -> None:
        """Optional: undo a step's side effects on pipeline failure."""
        ...


# ---------------------------------------------------------------------------
# §9.1f: Step Registry Singleton
# ---------------------------------------------------------------------------


STEP_REGISTRY: dict[str, type] = {}


class RegisteredStep:
    """Base class for concrete step implementations.

    Subclasses auto-register via __init_subclass__. Usage:

        class FetchStep(RegisteredStep):
            type_name = "fetch"
            side_effects = False
            class Params(BaseModel):
                provider: str
                data_type: str
    """

    type_name: str = ""
    side_effects: bool = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.type_name:
            if cls.type_name in STEP_REGISTRY:
                raise ValueError(
                    f"Duplicate step type '{cls.type_name}': "
                    f"{STEP_REGISTRY[cls.type_name].__name__} vs {cls.__name__}"
                )
            STEP_REGISTRY[cls.type_name] = cls

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        raise NotImplementedError  # noqa: placeholder

    @classmethod
    def params_schema(cls) -> dict:
        if hasattr(cls, "Params"):
            return getattr(cls, "Params").model_json_schema()
        return {}

    async def compensate(
        self, params: dict, context: StepContext, prior_result: StepResult
    ) -> None:
        """Default: no compensation. Override for steps with side effects."""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_step(type_name: str) -> type | None:
    """Look up a registered step type by name."""
    return STEP_REGISTRY.get(type_name)


def has_step(type_name: str) -> bool:
    """Check if a step type is registered."""
    return type_name in STEP_REGISTRY


def list_steps() -> list[dict]:
    """List all registered step types with their schemas (for MCP exposure)."""
    return [
        {
            "type_name": cls.type_name,
            "side_effects": cls.side_effects,
            "params_schema": cls.params_schema(),
        }
        for cls in STEP_REGISTRY.values()
    ]


def get_all_steps() -> list[type["RegisteredStep"]]:
    """Return all registered step classes — used by REST API §9.5.

    Unlike list_steps() which returns serialized dicts for MCP,
    this returns the actual step classes for attribute access
    (e.g. s.type_name, s.Params.model_json_schema()).
    """
    return list(STEP_REGISTRY.values())
