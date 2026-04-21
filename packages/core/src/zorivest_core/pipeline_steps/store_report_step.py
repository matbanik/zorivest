# packages/core/src/zorivest_core/pipeline_steps/store_report_step.py
"""StoreReportStep — snapshot data and persist to report table (§9.6).

Spec: 09-scheduling.md §9.6a–c
MEU: 87
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from zorivest_core.domain.enums import PipelineStatus
from zorivest_core.domain.pipeline import StepContext, StepResult
from zorivest_core.domain.step_registry import RegisteredStep


class StoreReportStep(RegisteredStep):
    """Snapshot query results and persist to the reports table.

    Auto-registers as ``type_name="store_report"`` in the step registry.
    """

    type_name = "store_report"
    side_effects = True

    class Params(BaseModel):
        """StoreReportStep parameter schema."""

        model_config = {"extra": "forbid"}

        report_name: str = Field(..., description="Name of the report to create/update")
        spec: dict[str, Any] = Field(
            default_factory=dict,
            description="Report specification (sections, layout)",
        )
        data_queries: list[dict[str, str]] = Field(
            default_factory=list,
            description="Named SQL queries: [{name: str, sql: str}, ...]",
        )

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        """Execute the store report step.

        1. Validate params
        2. Execute data queries via _execute_sandboxed_sql() hook
        3. Compute snapshot hash from serialized results
        4. Persist report via _persist_report() hook
        5. Return report metadata with snapshot hash and report_id
        """
        import hashlib
        import json

        p = self.Params(**params)

        # 1. Execute data queries via sandboxed SQL
        snapshots = self._execute_sandboxed_sql(p.data_queries, context)

        # 2. Compute snapshot hash
        snapshot_json = json.dumps(
            snapshots,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        snapshot_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()

        # 3. Serialize the authored report spec (distinct from snapshot)
        spec_json = json.dumps(
            p.spec,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        # 4. Persist report via repository hook
        report_id = self._persist_report(
            report_name=p.report_name,
            spec_json=spec_json,
            snapshot_json=snapshot_json,
            snapshot_hash=snapshot_hash,
            context=context,
        )

        return StepResult(
            status=PipelineStatus.SUCCESS,
            output={
                "report_name": p.report_name,
                "report_id": report_id,
                "snapshot_hash": snapshot_hash,
                "snapshot_json": snapshot_json,
                "spec_json": spec_json,
                "query_count": len(p.data_queries),
            },
        )

    def _execute_sandboxed_sql(
        self,
        data_queries: list[dict[str, str]],
        context: StepContext,
    ) -> dict[str, Any]:
        """Execute data queries via sandboxed SQL connection.

        Looks for 'db_connection' in context.outputs. Raises ValueError
        if queries are provided but no connection is available.
        """
        db_conn = context.outputs.get("db_connection")

        if not data_queries:
            return {}

        if db_conn is None:
            raise ValueError(
                "db_connection required in context.outputs when data_queries"
                " is non-empty for StoreReportStep"
            )

        # db_conn is narrowed to non-None beyond this point
        snapshots: dict[str, Any] = {}

        for query_def in data_queries:
            name = query_def.get("name", "unnamed")
            sql = query_def.get("sql", "")

            if sql:
                cursor = db_conn.execute(sql)
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                snapshots[name] = {"sql": sql, "rows": rows}
            else:
                snapshots[name] = {"sql": sql, "rows": []}

        return snapshots

    def _persist_report(
        self,
        *,
        report_name: str,
        spec_json: str,
        snapshot_json: str,
        snapshot_hash: str,
        context: StepContext,
    ) -> str | None:
        """Persist the report via ReportRepository.

        Requires 'report_repository' in context.outputs. Raises ValueError
        if the repository is not injected.
        """
        report_repo = context.outputs.get("report_repository")
        if report_repo is None:
            raise ValueError(
                "report_repository required in context.outputs for StoreReportStep"
            )
        return report_repo.create(
            name=report_name,
            spec_json=spec_json,
            snapshot_json=snapshot_json,
            snapshot_hash=snapshot_hash,
        )
