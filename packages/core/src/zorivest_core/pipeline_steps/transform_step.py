# packages/core/src/zorivest_core/pipeline_steps/transform_step.py
"""TransformStep — transforms and validates market data (§9.5).

Spec: 09-scheduling.md §9.5a–e
MEU: 86, PW12

PW12 enhancements:
  AC-1: Dynamic source resolution via source_step_id param
  AC-5: Record enrichment with provider/timestamp
  AC-6: Configurable output_key + presentation mapping
  AC-8: Zero-record WARNING with min_records > 0
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep

logger = structlog.get_logger(__name__)

# Presentation mapping: canonical → template-friendly names (AC-6)
_PRESENTATION_MAP: dict[str, str] = {
    "ticker": "symbol",
    "last": "price",
}


class TransformStep(RegisteredStep):
    """Transform raw market data: map fields, validate, write to DB.

    Auto-registers as ``type_name="transform"`` in the step registry.
    """

    type_name = "transform"
    side_effects = True

    class Params(BaseModel):
        """TransformStep parameter schema."""

        model_config = {"extra": "forbid"}

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
        # AC-1: Dynamic source resolution
        source_step_id: str | None = Field(
            default=None,
            description=(
                "Step ID to read source data from. "
                "When None, falls back to 'fetch_result' for backward compatibility."
            ),
        )
        # AC-6: Configurable output key for downstream steps
        output_key: str = Field(
            default="records",
            description="Key under which validated records are stored in step output",
        )
        # AC-8: Minimum records threshold for warning
        min_records: int = Field(
            default=0,
            ge=0,
            description=(
                "Minimum expected record count. "
                "0 records with min_records > 0 returns WARNING status."
            ),
        )

    @staticmethod
    def _resolve_source(
        source_step_id: str | None,
        context: StepContext,
    ) -> dict:
        """Resolve the source step output for this transform.

        Resolution priority:
        1. Explicit ``source_step_id`` — direct lookup in context.outputs.
        2. Auto-discovery — scan context.outputs for dicts with both
           ``content`` and ``provider`` keys (FetchStep output signature).
        3. Legacy fallback — look for ``"fetch_result"`` for backward compat.

        Returns an empty dict if nothing matches (handled downstream as
        0-records WARNING).
        """
        import logging

        logger = logging.getLogger(__name__)

        # 1. Explicit source_step_id
        if source_step_id:
            return context.outputs.get(source_step_id, {})

        # 2. Auto-discover by FetchStep output shape
        for key, value in context.outputs.items():
            if isinstance(value, dict) and "content" in value and "provider" in value:
                logger.debug(
                    "TransformStep: auto-discovered fetch output under key '%s'",
                    key,
                )
                return value

        # 3. Legacy fallback
        return context.outputs.get("fetch_result", {})

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the transform step.

        1. Resolve source data dynamically (AC-1)
        2. Extract records from provider envelope (AC-2)
        3. Apply field mapping
        4. Enrich records with provider/timestamp (AC-5)
        5. Validate via Pandera schema
        6. Apply presentation mapping (AC-6)
        7. Check quality threshold
        8. Write to target table
        9. Return records under output_key (AC-6)
        10. Warn on zero records if min_records > 0 (AC-8)
        """
        import pandas as pd

        from zorivest_core.services.validation_gate import (
            check_quality,
            validate_dataframe,
        )

        p = self.Params(**params)

        # 1. Resolve source data (AC-1)
        source_output = self._resolve_source(p.source_step_id, context)

        # Get raw content from source step output
        source_content = (
            source_output.get("content", b"")
            if isinstance(source_output, dict)
            else b""
        )
        provider = (
            source_output.get("provider") if isinstance(source_output, dict) else None
        )
        data_type = (
            source_output.get("data_type") if isinstance(source_output, dict) else None
        )

        # 2. Extract records (AC-2: use response extractors for envelope unwrapping)
        records = self._extract_records(source_content, provider, data_type)

        if not records:
            # AC-8: Zero-record warning
            status = PipelineStatus.SUCCESS
            if p.min_records > 0:
                status = PipelineStatus.WARNING
                logger.warning(
                    "transform_zero_records",
                    source_step_id=p.source_step_id,
                    min_records=p.min_records,
                    target_table=p.target_table,
                )

            return StepResult(
                status=status,
                output={
                    "target_table": p.target_table,
                    "write_disposition": p.write_disposition,
                    "records_written": 0,
                    "records_quarantined": 0,
                    "quality_ratio": 0.0,
                    p.output_key: [],
                },
            )

        # 3. Apply field mapping
        records = self._apply_mapping(records, provider, data_type)

        # 4. Enrich records with provider/timestamp (AC-5)
        records = self._enrich_records(records, provider)

        # 5. Create DataFrame and validate
        df = pd.DataFrame(records)
        valid_df, quarantined_df = validate_dataframe(df, p.validation_rules)

        # 6. Check quality threshold
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
                    p.output_key: [],
                },
            )

        # 7. Write to target table via hook method
        #    Drop _extra before write — it's a passthrough bag for unmapped
        #    provider fields, not a DB column.
        write_df = valid_df.drop(columns=["_extra"], errors="ignore")
        records_written = self._write_data(
            write_df,
            p.target_table,
            p.write_disposition,
            context,
        )

        # 8. Apply presentation mapping + prepare output records (AC-6)
        output_records = self._apply_presentation_mapping(valid_df.to_dict("records"))

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={
                "target_table": p.target_table,
                "write_disposition": p.write_disposition,
                "records_written": records_written,
                "records_quarantined": len(quarantined_df),
                "quality_ratio": quality["ratio"],
                p.output_key: output_records,
            },
        )

    def _extract_records(
        self,
        source_content: Any,
        provider: str | None,
        data_type: str | None,
    ) -> list[dict]:
        """Extract records from raw source content.

        Uses response_extractors if available, falls back to basic JSON parse.
        """
        import json

        if isinstance(source_content, bytes):
            if not source_content:
                return []
            # Try provider-specific extraction first (AC-2)
            if provider and data_type:
                try:
                    from zorivest_infra.market_data.response_extractors import (
                        extract_records,
                    )

                    return extract_records(source_content, provider, data_type)
                except ImportError:
                    pass  # Infrastructure not available

            # Fallback: basic JSON parse
            try:
                data = json.loads(source_content)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return [data]
            except (json.JSONDecodeError, UnicodeDecodeError):
                return []
        elif isinstance(source_content, list):
            return source_content
        return []

    def _apply_mapping(
        self,
        records: list[dict],
        provider: str | None,
        data_type: str | None,
    ) -> list[dict]:
        """Apply field mapping to raw records (AC-3 compatible).

        Only applies if a mapping is registered for the provider+data_type.
        Otherwise returns records unchanged to avoid stuffing all fields
        into ``_extra``.
        """
        if provider and data_type:
            try:
                from zorivest_infra.market_data.field_mappings import (
                    FIELD_MAPPINGS,
                    _PROVIDER_SLUG_MAP,
                    apply_field_mapping,
                )

                slug = _PROVIDER_SLUG_MAP.get(provider, provider)
                if (slug, data_type) not in FIELD_MAPPINGS:
                    return records  # No mapping registered — pass through

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

    def _enrich_records(
        self,
        records: list[dict],
        provider: str | None,
    ) -> list[dict]:
        """Enrich records with provider and timestamp metadata (AC-5).

        Only enriches if provider is available. Skips gracefully otherwise.
        """
        if not provider:
            return records

        now = datetime.now(timezone.utc).isoformat()
        for r in records:
            if "provider" not in r:
                r["provider"] = provider
            if "timestamp" not in r:
                r["timestamp"] = now
        return records

    @staticmethod
    def _apply_presentation_mapping(records: list[dict]) -> list[dict]:
        """Rename canonical fields to template-friendly names (AC-6).

        ticker → symbol, last → price.
        """
        result = []
        for record in records:
            mapped = {}
            for k, v in record.items():
                new_key = _PRESENTATION_MAP.get(k, k)
                mapped[new_key] = v
            result.append(mapped)
        return result

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
