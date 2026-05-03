from dataclasses import dataclass, field

from enums import CardKeyword, CardRarity, CardStatusId, CardType


@dataclass(frozen=True, slots=True, kw_only=True)
class CardTemplate:
    id: int
    name: str
    rarity: CardRarity
    cost: int
    keywords: CardKeyword
    statuses: dict[CardStatusId, int] = field(default_factory=dict)

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

    @property
    def type(self) -> CardType:
        return CardType.MONSTER


@dataclass(frozen=True, slots=True, kw_only=True)
class SpellTemplate(CardTemplate):
    @property
    def type(self) -> CardType:
        return CardType.SPELL
