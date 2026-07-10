from dataclasses import dataclass

from deltacards.actions.results import ActionResult


@dataclass(slots=True)
class ActionLogRecord:
    id: int

    action_name: str
    results: tuple[ActionResult, ...]

    group_id: int
    parent_id: int | None
    depth: int
