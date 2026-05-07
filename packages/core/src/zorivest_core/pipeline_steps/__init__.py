# packages/core/src/zorivest_core/pipeline_steps/__init__.py
"""Pipeline step implementations (Phase 9).

Eagerly imports all concrete step modules to populate STEP_REGISTRY
at import time. After ``import zorivest_core.pipeline_steps``,
``get_step("fetch")`` etc. work immediately.

Spec: 09-scheduling.md §9.4–§9.7
"""

from zorivest_core.pipeline_steps import fetch_step  # noqa: F401
from zorivest_core.pipeline_steps import transform_step  # noqa: F401
from zorivest_core.pipeline_steps import store_report_step  # noqa: F401
from zorivest_core.pipeline_steps import render_step  # noqa: F401
from zorivest_core.pipeline_steps import send_step  # noqa: F401
from zorivest_core.pipeline_steps import query_step  # noqa: F401
from zorivest_core.pipeline_steps import compose_step  # noqa: F401
from zorivest_core.pipeline_steps import market_data_store_step  # noqa: F401
