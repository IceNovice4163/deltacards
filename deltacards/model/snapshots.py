from dataclasses import dataclass
from typing import TYPE_CHECKING

from deltacards.model.enums import CardKeyword, CardStatusId, CardType, CardZone, Tribe

if TYPE_CHECKING:
    from deltacards.model.cards import CardBuffs, CardTemplate, CaughtCardData


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

    def has_keyword(self, keyword: CardKeyword) -> bool:
        return keyword in self.keywords

    def get_status(self, status_id: CardStatusId) -> int:
        return self.statuses.get(status_id, 0)


@dataclass(frozen=True, slots=True, kw_only=True)
class MonsterSnapshot(CardSnapshot):
    age: int
    has_attacked: bool
    hp_missing: int

    pos: int | None
    attack: int
    hp: int
    max_hp: int

    def has_tribe(self, tribe: Tribe) -> bool:
        return (tribe in self.template.tribes) or (Tribe.ALL in self.template.tribes)


@dataclass(frozen=True, slots=True, kw_only=True)
class SpellSnapshot(CardSnapshot):
    pass
