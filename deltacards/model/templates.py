from dataclasses import dataclass

from deltacards.model.enums import (
    CardKeyword,
    CardRarity,
    CardStatusId,
    CardType,
    Tribe,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CardTemplate:
    id: int
    name: str
    rarity: CardRarity
    cost: int
    keywords: CardKeyword
    statuses: dict[CardStatusId, int]

    @property
    def base_identity(self) -> tuple[str, int]:
        return 'card', self.id

    @property
    def type(self) -> CardType:
        raise NotImplementedError


@dataclass(frozen=True, slots=True, kw_only=True)
class MonsterTemplate(CardTemplate):
    attack: int
    hp: int
    tribes: tuple[Tribe, ...]

    @property
    def type(self) -> CardType:
        return CardType.MONSTER


@dataclass(frozen=True, slots=True, kw_only=True)
class SpellTemplate(CardTemplate):
    @property
    def type(self) -> CardType:
        return CardType.SPELL
