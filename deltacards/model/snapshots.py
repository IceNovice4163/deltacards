from dataclasses import dataclass
from typing import TYPE_CHECKING

from deltacards.model.enums import CardKeyword, CardStatusId, CardToggleableAbility, CardType, CardZone, PlayerId, Tribe

if TYPE_CHECKING:
    from deltacards.model.cards import BaseStats, CardBuffs, CardTemplate, CaughtCardData


@dataclass(frozen=True, slots=True, kw_only=True)
class EntitySnapshot:
    id: PlayerId | int


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerSnapshot(EntitySnapshot):
    id: PlayerId
    gold: int
    hp: int
    max_hp: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CardSnapshot(EntitySnapshot):
    id: int
    type: CardType
    template: 'CardTemplate'
    controller_id: PlayerId
    base: BaseStats
    keywords: CardKeyword
    statuses: dict[CardStatusId, int]
    active_abilities: set[CardToggleableAbility]
    buffs: 'CardBuffs'
    caught_card: 'CaughtCardData | None'

    zone: CardZone
    creator_id: int
    creator_base_identity: tuple[str, int] | None
    cost: int

    @property
    def is_generated(self) -> bool:
        return self.creator_id is not None

    def has_keyword(self, keyword: CardKeyword) -> bool:
        return keyword in self.keywords

    def get_status(self, status_id: CardStatusId) -> int:
        return self.statuses.get(status_id, 0)

    def has_tribe(self, tribe: Tribe) -> bool:
        return (tribe in self.template.tribes) or (Tribe.ALL in self.template.tribes)


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


@dataclass(frozen=True, slots=True, kw_only=True)
class SoulSnapshot(EntitySnapshot):
    id: int
    name: str
    controller_id: PlayerId


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactSnapshot(EntitySnapshot):
    id: int
    name: str
    controller_id: PlayerId
    counter: int
    active: bool
