# packages/core/src/zorivest_core/domain/report_spec.py
"""ReportSpec DSL — Pydantic models for report layout (§9.6b).

Supports discriminated union sections:
- DataTableSection: tabular data from SQL query
- MetricCardSection: single-value metric display
- ChartSection: chart visualization (candlestick, etc.)

Spec: 09-scheduling.md §9.6b
MEU: 87
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class DataTableSection(BaseModel):
    """Tabular data section rendered from a SQL query."""

    section_type: Literal["data_table"] = "data_table"
    title: str = Field(..., min_length=1, max_length=128)
    query: str = Field(..., description="SQL query for data")
    max_rows: int = Field(default=100, ge=1, le=1000)
    sortable: bool = True


class MetricCardSection(BaseModel):
    """Single-value metric display."""

    section_type: Literal["metric_card"] = "metric_card"
    title: str = Field(..., min_length=1, max_length=128)
    query: str = Field(..., description="SQL query returning single value")
    label: str = Field(..., description="Display label for the metric")
    format: str = Field(default="auto", description="Display format: 'currency', 'percent', 'number', 'auto'")


class ChartSection(BaseModel):
    """Chart visualization section."""

    section_type: Literal["chart"] = "chart"
    title: str = Field(..., min_length=1, max_length=128)
    chart_type: str = Field(
        ..., description="Chart type: 'candlestick', 'line', 'bar', 'pie'"
    )
    query: str = Field(..., description="SQL query for chart data")
    width: int = Field(default=800, ge=200, le=2000)
    height: int = Field(default=400, ge=200, le=1200)


# Discriminated union of all section types
SectionType = Annotated[
    Union[DataTableSection, MetricCardSection, ChartSection],
    Field(discriminator="section_type"),
]


class ReportSpec(BaseModel):
    """Report specification — defines layout and data sources."""

    name: str = Field(..., min_length=1, max_length=256)
    sections: list[SectionType] = Field(default_factory=list, max_length=20)
    description: str = Field(default="", max_length=500)
