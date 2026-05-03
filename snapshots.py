from dataclasses import dataclass
from typing import TYPE_CHECKING

from enums import CardKeyword, CardStatusId, CardType, CardZone

if TYPE_CHECKING:
    from cards import CardBuffs, CardTemplate, CaughtCardData


@dataclass(frozen=True, slots=True, kw_only=True)
class EntitySnapshot:
    id: int


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerSnapshot(EntitySnapshot):
    gold: int
    hp: int
    max_hp: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CardSnapshot(EntitySnapshot):
    type: CardType
    template: 'CardTemplate'
    controller_id: int
    keywords: CardKeyword
    statuses: dict[CardStatusId, int]
    buffs: 'CardBuffs'
    caught_card: 'CaughtCardData | None'

    zone: CardZone
    creator_id: int
    creator_base_identity: tuple[str, int] | None
    cost: int


@dataclass(frozen=True, slots=True, kw_only=True)
class MonsterSnapshot(CardSnapshot):
    age: int
    has_attacked: bool
    hp_missing: int

    pos: int | None
    attack: int
    hp: int
    max_hp: int


@dataclass(frozen=True, slots=True, kw_only=True)
class SpellSnapshot(CardSnapshot):
    pass
