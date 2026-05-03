from dataclasses import dataclass

from enums import DamageKind, PlayerId
from snapshots import EntitySnapshot, MonsterSnapshot, PlayerSnapshot

__all__ = (
    'ActionResult',
    'EntityDamagedResult', 'EntityHealedResult',
    'AttackAftermathResult',
    'MonsterSummonedResult',
    'MonsterKilledResult', 'PlayerKilledResult',
    'SpentGoldResult',
)


@dataclass(slots=True, kw_only=True)
class ActionResult:
    # Filled by Game when recorded
    id: int = -1
    turn: int = -1
    turn_player_id: PlayerId = -1

    source_id: int | None = None
    group_id: int | None = None


@dataclass(slots=True, kw_only=True)
class EntityDamagedResult(ActionResult):
    target_id: int
    target: MonsterSnapshot | PlayerSnapshot
    amount: int
    killed: bool
    excess_damage: int
    kind: DamageKind


@dataclass(slots=True, kw_only=True)
class EntityHealedResult(ActionResult):
    target_id: int
    target: MonsterSnapshot | PlayerSnapshot
    amount: int


@dataclass(slots=True, kw_only=True)
class AttackAftermathResult(ActionResult):
    attacker_id: int
    attacker: MonsterSnapshot
    defender_id: int
    defender: MonsterSnapshot | PlayerSnapshot

    damage_to_attacker: int
    damage_to_defender: int

    attacker_dead: bool
    defender_dead: bool


@dataclass(slots=True, kw_only=True)
class MonsterSummonedResult(ActionResult):
    monster_id: int
    monster: MonsterSnapshot


@dataclass(slots=True, kw_only=True)
class MonsterKilledResult(ActionResult):
    monster_id: int
    monster: MonsterSnapshot
    killer_id: int
    killer: EntitySnapshot


@dataclass(slots=True, kw_only=True)
class PlayerKilledResult(ActionResult):
    player_id: int
    player: PlayerSnapshot
    killer_id: int
    killer: EntitySnapshot


@dataclass(slots=True, kw_only=True)
class SpentGoldResult(ActionResult):
    player_id: int
    amount: int
    spent_on_spell: bool
