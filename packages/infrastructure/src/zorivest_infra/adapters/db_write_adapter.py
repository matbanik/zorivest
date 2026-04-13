# packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py
"""DbWriteAdapter — bridges TransformStep to write_dispositions functions (§9.5d).

TransformStep._write_data() calls: db_writer.write(df, table, disposition)
This adapter converts that interface to the write_dispositions module's
function-based API: write_append/write_replace/write_merge.

Spec: 09-scheduling.md §9.5d
MEU: PW1
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from zorivest_infra.repositories.write_dispositions import (
    write_append,
    write_merge,
    write_replace,
)


class DbWriteAdapter:
    """Thin adapter wrapping write_dispositions functions.

    Accepts the same call interface as TransformStep._write_data() expects:
      write(df=..., table=..., disposition=..., key_columns=...)

    Dispatches to the appropriate write_dispositions function based on
    the disposition parameter.
    """

    def __init__(self, *, session: Session) -> None:
        self._session = session

    def write(
        self,
        *,
        df: Any,
        table: str,
        disposition: str,
        key_columns: list[str] | None = None,
    ) -> int:
        """Write DataFrame records to denormalized table.

        Args:
            df: Object with .to_dict(orient="records") method (e.g. pandas DataFrame).
            table: Target table name (must be in TABLE_ALLOWLIST).
            disposition: Write mode — "append", "replace", or "merge".
            key_columns: Required when disposition is "merge".

        Returns:
            Number of records written.

        Raises:
            ValueError: If disposition is unknown or merge is missing key_columns.
        """
        records: list[dict[str, Any]] = df.to_dict(orient="records")

        if disposition == "append":
            return write_append(
                session=self._session,
                table_name=table,
                records=records,
            )
        elif disposition == "replace":
            return write_replace(
                session=self._session,
                table_name=table,
                records=records,
            )
        elif disposition == "merge":
            if not key_columns:
                raise ValueError("key_columns required for 'merge' write disposition")
            return write_merge(
                session=self._session,
                table_name=table,
                records=records,
                key_columns=key_columns,
            )
        else:
            raise ValueError(
                f"Unknown write disposition: '{disposition}'. "
                f"Valid options: 'append', 'replace', 'merge'"
            )
