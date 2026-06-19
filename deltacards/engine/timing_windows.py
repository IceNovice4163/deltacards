from dataclasses import dataclass, field
from typing import Any, Literal

from deltacards.actions.base import ActionContext
from deltacards.actions.standard import (
    AdvanceTurn,
    DrawNext,
    PlayerStartTurnAction,
    ResolveScheduledEffectsAction,
    TriggerAbility,
)
from deltacards.engine.effects import EffectStep
from deltacards.model.cards import CardZone, Monster
from deltacards.model.entity import Entity
from deltacards.model.enums import Ability
from deltacards.model.player import Player

BucketName = Literal['monster', 'soul', 'artifact']
BUCKET_ORDER: tuple[BucketName, ...] = ('monster', 'soul', 'artifact')


@dataclass(frozen=True, slots=True)
class TimedWindowEntry:
    bucket: BucketName
    source_id: int
    kwargs: dict[str, Any] = field(default_factory=dict)


def _snapshot_bucket(player: Player, bucket: BucketName) -> list[TimedWindowEntry]:
    if bucket == 'monster':
        return [
            TimedWindowEntry(bucket='monster', source_id=m.id)
            for m in list(player.board.cards)
        ]

    if bucket == 'soul':
        return [
            TimedWindowEntry(
                bucket='soul',
                source_id=player.soul.id,
                kwargs={'owner': player},
            )
        ]

    if bucket == 'artifact':
        return [
            TimedWindowEntry(
                bucket='artifact',
                source_id=artifact.id,
                kwargs={'owner': player},
            )
            for artifact in list(player.artifacts)
        ]

    raise ValueError(f"Invalid bucket: {bucket}")


def _resolve_valid_source(entry: TimedWindowEntry, ctx: ActionContext, player: Player) -> Entity | None:
    """
    Evaluate the entry and check if trigger source is still valid.
    Returns None if entry is no longer a valid source.
    """
    if entry.bucket == 'monster':
        entity = ctx.game.entities[entry.source_id]
        if not isinstance(entity, Monster):
            return None
        if entity.zone is not CardZone.BOARD:
            return None
        if entity.controller_id != player.id:
            return None
        return entity

    if entry.bucket == 'soul':
        return player.soul

    if entry.bucket == 'artifact':
        for artifact in player.artifacts:
            if artifact.id == entry.source_id:
                return artifact
        return None

    raise ValueError(f"Invalid bucket: {entry.bucket}")


def run_timed_ability_window(ctx: ActionContext, player: Player, ability: Ability):
    """
    Run a timed ability window (Turn Start / Turn End) in ordered buckets.
    Each bucket is snapshotted only when reached, so earlier buckets may affect later ones.
    Within a bucket, new triggers cannot be added, and triggers whose source becomes invalid are skipped.
    Example: a monster summoned by a Turn End effect will not trigger its own Turn End this turn.
    """
    for bucket in BUCKET_ORDER:
        entries = _snapshot_bucket(player, bucket)

        for entry in entries:
            source = _resolve_valid_source(entry, ctx, player)
            if source is None:
                continue

            if entry.kwargs:
                yield EffectStep(
                    [TriggerAbility(target=source, ability=ability)],
                    kwargs=entry.kwargs.copy(),
                )
            else:
                yield TriggerAbility(target=source, ability=ability)


def run_player_start_turn_window(ctx: ActionContext, player: Player):
    player.turn += 1
    player.increase_gold(player.turn)

    for monster in list(player.board.cards):
        monster.on_turn_start()

    yield DrawNext(player=player, reason='turn_start')

    # Resolve Turn Start effects
    yield from run_timed_ability_window(ctx=ctx, player=player, ability=Ability.TURN_START)


def run_player_end_turn_window(ctx: ActionContext, player: Player):
    for monster in list(player.board.cards):
        monster.on_turn_end()

    # Resolve pending Delay effects
    yield ResolveScheduledEffectsAction(player=player)

    # Resolve Turn End effects
    yield from run_timed_ability_window(ctx=ctx, player=player, ability=Ability.TURN_END)

    # Pass the turn
    yield AdvanceTurn(player=player)
    yield PlayerStartTurnAction(player=player.opponent)
