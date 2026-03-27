# packages/core/src/zorivest_core/pipeline_steps/transform_step.py
"""TransformStep — transforms and validates market data (§9.5).

Spec: 09-scheduling.md §9.5a–e
MEU: 86
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep


class TransformStep(RegisteredStep):
    """Transform raw market data: map fields, validate, write to DB.

    Auto-registers as ``type_name="transform"`` in the step registry.
    """

    type_name = "transform"
    side_effects = True

    class Params(BaseModel):
        """TransformStep parameter schema."""

        target_table: str = Field(..., description="Target table for transformed data")
        mapping: str = Field(
            default="auto",
            description="Field mapping strategy: 'auto' or provider-specific key",
        )
        write_disposition: str = Field(
            default="append",
            description="Write mode: 'append', 'replace', or 'merge'",
        )
        validation_rules: str = Field(
            default="ohlcv",
            description="Validation schema name to apply",
        )
        quality_threshold: float = Field(
            default=0.8,
            ge=0.0,
            le=1.0,
            description="Minimum ratio of valid records to proceed",
        )

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the transform step.

        1. Get source data from prior step
        2. Apply field mapping via _apply_mapping() hook
        3. Validate via Pandera schema
        4. Check quality threshold
        5. Write to target table via _write_data() hook
        """
        import json

        import pandas as pd

        from zorivest_core.services.validation_gate import (
            check_quality,
            validate_dataframe,
        )

        p = self.Params(**params)

        # 1. Get source data from prior step output in context
        source_content = context.outputs.get("fetch_result", {}).get("content", b"")
        if isinstance(source_content, bytes):
            try:
                records = json.loads(source_content) if source_content else []
            except (json.JSONDecodeError, UnicodeDecodeError):
                records = []
        elif isinstance(source_content, list):
            records = source_content
        else:
            records = []

        if not records:
            return StepResult(
                status=PipelineStatus.SUCCESS,
                output={
                    "target_table": p.target_table,
                    "write_disposition": p.write_disposition,
                    "records_written": 0,
                    "records_quarantined": 0,
                    "quality_ratio": 0.0,
                },
            )

        # 2. Apply field mapping if provider info available
        records = self._apply_mapping(records, context)

        # 3. Create DataFrame and validate
        df = pd.DataFrame(records)
        valid_df, quarantined_df = validate_dataframe(df, p.validation_rules)

        # 4. Check quality threshold
        quality = check_quality(len(valid_df), len(df), p.quality_threshold)
        if not quality["passed"]:
            return StepResult(
                status=PipelineStatus.FAILED,
                error=(
                    f"Quality {quality['ratio']:.0%} below "
                    f"threshold {p.quality_threshold:.0%}"
                ),
                output={
                    "target_table": p.target_table,
                    "records_valid": len(valid_df),
                    "records_quarantined": len(quarantined_df),
                    "quality_ratio": quality["ratio"],
                },
            )

        # 5. Write to target table via hook method
        records_written = self._write_data(
            valid_df,
            p.target_table,
            p.write_disposition,
            context,
        )

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={
                "target_table": p.target_table,
                "write_disposition": p.write_disposition,
                "records_written": records_written,
                "records_quarantined": len(quarantined_df),
                "quality_ratio": quality["ratio"],
            },
        )

    def _apply_mapping(
        self,
        records: list[dict],
        context: StepContext,
    ) -> list[dict]:
        """Apply field mapping to raw records.

        Looks for provider/data_type info in context.outputs["fetch_result"]
        and uses apply_field_mapping() from infrastructure if available.
        """
        fetch_info = context.outputs.get("fetch_result", {})
        provider = fetch_info.get("provider")
        data_type = fetch_info.get("data_type")

        if provider and data_type:
            try:
                from zorivest_infra.market_data.field_mappings import (
                    apply_field_mapping,
                )

                return [
                    apply_field_mapping(
                        record=r,
                        provider=provider,
                        data_type=data_type,
                    )
                    for r in records
                ]
            except ImportError:
                pass  # Infrastructure not available — skip mapping
        return records

    def _write_data(
        self,
        df: Any,
        target_table: str,
        write_disposition: str,
        context: StepContext,
    ) -> int:
        """Write validated data to the target table.

        Requires 'db_writer' in context.outputs. Raises ValueError
        if the writer is not injected.
        """
        db_writer = context.outputs.get("db_writer")
        if db_writer is None:
            raise ValueError("db_writer required in context.outputs for TransformStep")
        return db_writer.write(
            df=df,
            table=target_table,
            disposition=write_disposition,
        )
