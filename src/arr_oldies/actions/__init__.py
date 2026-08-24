"""Safe action engine package for dry-run simulation, execution plans, and mutation execution."""

from arr_oldies.actions.confirmation import (
    prompt_confirmation,
    render_confirmation_panel,
    render_dry_run_table,
    render_execution_report_table,
)
from arr_oldies.actions.executor import ActionExecutor
from arr_oldies.actions.models import (
    ActionItem,
    ActionPlan,
    ActionResult,
    ActionType,
    ExecutionReport,
)

__all__ = [
    "ActionExecutor",
    "ActionItem",
    "ActionPlan",
    "ActionResult",
    "ActionType",
    "ExecutionReport",
    "prompt_confirmation",
    "render_confirmation_panel",
    "render_dry_run_table",
    "render_execution_report_table",
]
