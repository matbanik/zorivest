"""Shared schemas for the REST API.

Source: 04-rest-api.md §Shared Schemas
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination envelope for list endpoints."""

    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorEnvelope(BaseModel):
    """Standard error response format."""

    error: str
    detail: str
    request_id: str
