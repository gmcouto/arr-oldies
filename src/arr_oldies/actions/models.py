"""Data models for safe action engine (dry-run simulation, execution plans, reports)."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from arr_oldies.inventory.models import MediaInventoryItem


class ActionType(StrEnum):
    """Supported mutation actions across Radarr and Sonarr instances."""

    DELETE = "delete"
    UNMONITOR = "unmonitor"
    UNMONITOR_SEASON = "unmonitor_season"
    UNMONITOR_SERIES = "unmonitor_series"
    REMOVE = "remove"


class ActionItem(BaseModel):
    """Association of a specific media inventory item with its designated actions."""

    model_config = ConfigDict(extra="ignore")

    item: MediaInventoryItem
    action_types: list[ActionType] = Field(default_factory=list)


class ActionPlan(BaseModel):
    """Complete simulation plan before execution, capturing items and projected impact."""

    model_config = ConfigDict(extra="ignore")

    target_actions: list[ActionType] = Field(default_factory=list)
    items: list[ActionItem] = Field(default_factory=list)
    total_items: int = 0
    total_size_bytes: int = 0
    instances_breakdown: dict[str, int] = Field(default_factory=dict)
    dry_run: bool = True


class ActionResult(BaseModel):
    """Result of an individual mutation action executed against a media item."""

    model_config = ConfigDict(extra="ignore")

    item_id: str
    instance_name: str
    action_type: ActionType
    success: bool
    freed_bytes: int = 0
    error_message: str | None = None


class ExecutionReport(BaseModel):
    """Aggregated report of executed mutation actions."""

    model_config = ConfigDict(extra="ignore")

    mode: str = "execute"
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    target_actions: list[ActionType] = Field(default_factory=list)
    total_attempted: int = 0
    successful_count: int = 0
    failed_count: int = 0
    total_freed_bytes: int = 0
    results: list[ActionResult] = Field(default_factory=list)
    duration_seconds: float = 0.0

    @field_validator("executed_at", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        """Ensure executed_at is in UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)
