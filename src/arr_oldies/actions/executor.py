"""Action planning, dry-run simulation engine, and JSON plan exporter."""

import json
from typing import Any

from arr_oldies.actions.models import (
    ActionItem,
    ActionPlan,
    ActionResult,
    ActionType,
    ExecutionReport,
)
from arr_oldies.inventory.models import MediaInventoryItem, MediaType
from arr_oldies.reporting.formatters import format_size


class ActionExecutor:
    """Simulation planner and mutation execution engine for *arr media items."""

    def build_plan(
        self,
        items: list[MediaInventoryItem],
        actions: list[ActionType],
        dry_run: bool = True,
    ) -> ActionPlan:
        """Build an immutable simulation plan without executing mutations."""
        action_items: list[ActionItem] = []
        instances_breakdown: dict[str, int] = {}
        total_size_bytes = 0

        for item in items:
            applicable_actions = [
                act
                for act in actions
                if not (act == ActionType.UNMONITOR_EPISODE and item.media_type == MediaType.MOVIE)
            ]
            action_items.append(ActionItem(item=item, action_types=applicable_actions))
            instances_breakdown[item.instance_name] = instances_breakdown.get(item.instance_name, 0) + 1
            total_size_bytes += item.size_bytes

        return ActionPlan(
            target_actions=actions,
            items=action_items,
            total_items=len(action_items),
            total_size_bytes=total_size_bytes,
            instances_breakdown=instances_breakdown,
            dry_run=dry_run,
        )

    def export_plan_json(self, plan: ActionPlan, indent: int = 2) -> str:
        """Serialize ActionPlan into formatted JSON string."""
        payload: dict[str, Any] = {
            "metadata": {
                "mode": "dry-run" if plan.dry_run else "execute",
                "dry_run": plan.dry_run,
                "target_actions": [act.value for act in plan.target_actions],
            },
            "summary": {
                "total_items": plan.total_items,
                "total_size_bytes": plan.total_size_bytes,
                "total_size_human": format_size(plan.total_size_bytes),
                "instances_breakdown": plan.instances_breakdown,
            },
            "items": [
                {
                    "item": action_item.item.model_dump(mode="json"),
                    "action_types": [act.value for act in action_item.action_types],
                }
                for action_item in plan.items
            ],
        }
        return json.dumps(payload, indent=indent, default=str)
