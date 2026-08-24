"""Action planning, dry-run simulation engine, ordered execution engine, and JSON serializers."""

import json
import time
from typing import Any

from arr_oldies.actions.models import (
    ActionItem,
    ActionPlan,
    ActionResult,
    ActionType,
    ExecutionReport,
)
from arr_oldies.api.factory import create_client
from arr_oldies.inventory.models import MediaInventoryItem, MediaType
from arr_oldies.models import InstanceConfig, InstanceType
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

    async def execute_plan(
        self,
        plan: ActionPlan,
        instances: list[InstanceConfig],
    ) -> ExecutionReport:
        """Execute action mutations across target instances in strict safe order."""
        clients = {inst.name: create_client(inst) for inst in instances}
        start_time = time.perf_counter()
        results: list[ActionResult] = []
        unmonitored_series: set[tuple[str, int]] = set()

        try:
            for action_item in plan.items:
                item = action_item.item
                client = clients.get(item.instance_name)

                if client is None:
                    for act in action_item.action_types:
                        results.append(
                            ActionResult(
                                item_id=item.id,
                                instance_name=item.instance_name,
                                action_type=act,
                                success=False,
                                freed_bytes=0,
                                error_message=f"Instance '{item.instance_name}' not configured",
                            )
                        )
                    continue

                # Step 1: Unmonitor Movie or entire Series (D-04, ACT-03)
                if ActionType.UNMONITOR in action_item.action_types:
                    if item.instance_type == InstanceType.RADARR and item.movie_id is not None:
                        try:
                            ok = await client.unmonitor_movie(item.movie_id)
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.UNMONITOR,
                                    success=ok,
                                    freed_bytes=0,
                                    error_message=None if ok else "Unmonitor movie failed",
                                )
                            )
                        except Exception as exc:
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.UNMONITOR,
                                    success=False,
                                    freed_bytes=0,
                                    error_message=str(exc),
                                )
                            )
                    elif item.instance_type == InstanceType.SONARR and item.series_id is not None:
                        series_key = (item.instance_name, item.series_id)
                        if series_key not in unmonitored_series:
                            try:
                                ok = await client.unmonitor_series(item.series_id)
                                if ok:
                                    unmonitored_series.add(series_key)
                                results.append(
                                    ActionResult(
                                        item_id=item.id,
                                        instance_name=item.instance_name,
                                        action_type=ActionType.UNMONITOR,
                                        success=ok,
                                        freed_bytes=0,
                                        error_message=None if ok else "Unmonitor series failed",
                                    )
                                )
                            except Exception as exc:
                                results.append(
                                    ActionResult(
                                        item_id=item.id,
                                        instance_name=item.instance_name,
                                        action_type=ActionType.UNMONITOR,
                                        success=False,
                                        freed_bytes=0,
                                        error_message=str(exc),
                                    )
                                )
                        else:
                            # Deduplicated unmonitoring
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.UNMONITOR,
                                    success=True,
                                    freed_bytes=0,
                                    error_message=None,
                                )
                            )

                # Step 2: Unmonitor specific Episode(s) (ACT-04)
                if (
                    ActionType.UNMONITOR_EPISODE in action_item.action_types
                    and item.instance_type == InstanceType.SONARR
                    and item.episode_ids
                ):
                    try:
                        ok = await client.unmonitor_episodes(item.episode_ids)
                        results.append(
                            ActionResult(
                                item_id=item.id,
                                instance_name=item.instance_name,
                                action_type=ActionType.UNMONITOR_EPISODE,
                                success=ok,
                                freed_bytes=0,
                                error_message=None if ok else "Unmonitor episodes failed",
                            )
                        )
                    except Exception as exc:
                        results.append(
                            ActionResult(
                                item_id=item.id,
                                instance_name=item.instance_name,
                                action_type=ActionType.UNMONITOR_EPISODE,
                                success=False,
                                freed_bytes=0,
                                error_message=str(exc),
                            )
                        )

                # Step 3: Delete media file (ACT-02, C-02) when REMOVE is not requested
                if (
                    ActionType.DELETE in action_item.action_types
                    and ActionType.REMOVE not in action_item.action_types
                ):
                    if item.instance_type == InstanceType.RADARR and item.movie_file_id is not None:
                        try:
                            ok = await client.delete_movie_file(item.movie_file_id)
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.DELETE,
                                    success=ok,
                                    freed_bytes=item.size_bytes if ok else 0,
                                    error_message=None if ok else "Delete movie file failed",
                                )
                            )
                        except Exception as exc:
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.DELETE,
                                    success=False,
                                    freed_bytes=0,
                                    error_message=str(exc),
                                )
                            )
                    elif item.instance_type == InstanceType.SONARR and item.episode_file_id is not None:
                        try:
                            ok = await client.delete_episode_file(item.episode_file_id)
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.DELETE,
                                    success=ok,
                                    freed_bytes=item.size_bytes if ok else 0,
                                    error_message=None if ok else "Delete episode file failed",
                                )
                            )
                        except Exception as exc:
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.DELETE,
                                    success=False,
                                    freed_bytes=0,
                                    error_message=str(exc),
                                )
                            )

                # Step 4: Remove library entry (ACT-05)
                if ActionType.REMOVE in action_item.action_types:
                    delete_files = ActionType.DELETE in action_item.action_types
                    if item.instance_type == InstanceType.RADARR and item.movie_id is not None:
                        try:
                            ok = await client.delete_movie(item.movie_id, delete_files=delete_files)
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.REMOVE,
                                    success=ok,
                                    freed_bytes=item.size_bytes if (ok and delete_files) else 0,
                                    error_message=None if ok else "Remove movie failed",
                                )
                            )
                        except Exception as exc:
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.REMOVE,
                                    success=False,
                                    freed_bytes=0,
                                    error_message=str(exc),
                                )
                            )
                    elif item.instance_type == InstanceType.SONARR and item.series_id is not None:
                        try:
                            ok = await client.delete_series(item.series_id, delete_files=delete_files)
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.REMOVE,
                                    success=ok,
                                    freed_bytes=item.size_bytes if (ok and delete_files) else 0,
                                    error_message=None if ok else "Remove series failed",
                                )
                            )
                        except Exception as exc:
                            results.append(
                                ActionResult(
                                    item_id=item.id,
                                    instance_name=item.instance_name,
                                    action_type=ActionType.REMOVE,
                                    success=False,
                                    freed_bytes=0,
                                    error_message=str(exc),
                                )
                            )
        finally:
            for c in clients.values():
                await c.close()

        successful_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)
        total_freed_bytes = sum(r.freed_bytes for r in results if r.success)
        duration_seconds = round(time.perf_counter() - start_time, 3)

        return ExecutionReport(
            mode="execute",
            target_actions=plan.target_actions,
            total_attempted=len(results),
            successful_count=successful_count,
            failed_count=failed_count,
            total_freed_bytes=total_freed_bytes,
            results=results,
            duration_seconds=duration_seconds,
        )

    def export_report_json(self, report: ExecutionReport, indent: int = 2) -> str:
        """Serialize ExecutionReport into formatted JSON string."""
        payload: dict[str, Any] = {
            "metadata": {
                "mode": report.mode,
                "executed_at": report.executed_at.isoformat(),
                "target_actions": [act.value for act in report.target_actions],
                "duration_seconds": report.duration_seconds,
            },
            "summary": {
                "total_attempted": report.total_attempted,
                "successful_count": report.successful_count,
                "failed_count": report.failed_count,
                "total_freed_bytes": report.total_freed_bytes,
                "total_freed_human": format_size(report.total_freed_bytes),
            },
            "results": [result.model_dump(mode="json") for result in report.results],
        }
        return json.dumps(payload, indent=indent, default=str)
