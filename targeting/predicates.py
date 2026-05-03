from dataclasses import dataclass
from typing import TYPE_CHECKING

from action_results import SpentGoldResult
from cards import Card, Monster
from cards.templates import CardTemplate
from enums import CardKeyword, CardRarity, CardStatusId, CardType

from .core import Predicate
from .values import RARITY

if TYPE_CHECKING:
    from actions import ActionContext
    from entity import Entity
    from player import Player


@dataclass(frozen=True, slots=True, eq=False)
class IsTypePredicate(Predicate):
    expected_type: CardType

    def test(self, entity: Card | CardTemplate, ctx: 'ActionContext', **kwargs) -> bool:
        assert isinstance(entity, (Card, CardTemplate))
        if isinstance(entity, Card):
            entity = entity.template

        return entity.type == self.expected_type

    def __repr__(self) -> str:
        return "IS_MONSTER" if self.expected_type == CardType.MONSTER else "IS_SPELL"


@dataclass(frozen=True, slots=True, eq=False)
class DamagedPredicate(Predicate):
    def test(self, entity: 'Entity', ctx: 'ActionContext', **kwargs) -> bool:
        if not isinstance(entity, Monster):
            return False

        return entity.hp < entity.max_hp

    def __repr__(self) -> str:
        return "DAMAGED"


@dataclass(frozen=True, slots=True, eq=False)
class HasKeywordPredicate(Predicate):
    keyword: CardKeyword

    def test(self, entity: Card, ctx: 'ActionContext', **kwargs) -> bool:
        if not isinstance(entity, Card):
            return False

        return entity.has_keyword(self.keyword)

    def __repr__(self) -> str:
        return f"HAS_KEYWORD({self.keyword.name})"


@dataclass(frozen=True, slots=True, eq=False)
class HasStatusPredicate(Predicate):
    status_id: CardStatusId

    def test(self, entity: Card, ctx: 'ActionContext', **kwargs) -> bool:
        if not isinstance(entity, Card):
            return False

        return entity.get_status(self.status_id) > 0

    def __repr__(self) -> str:
        return f"HAS_STATUS({self.status_id.name})"


@dataclass(frozen=True, slots=True, eq=False)
class GeneratedPredicate(Predicate):
    generated: bool = True

    def test(self, entity: Card, ctx: 'ActionContext', **kwargs) -> bool:
        if not isinstance(entity, Card):
            return False

        return entity.is_generated if self.generated else (not entity.is_generated)

    def __repr__(self) -> str:
        return "GENERATED" if self.generated else "NON_GENERATED"


@dataclass(frozen=True, slots=True, eq=False)
class GeneratedByPredicate(Predicate):
    creator: 'Entity | CardTemplate'

    def test(self, entity: Card, ctx: 'ActionContext', **kwargs) -> bool:
        if not isinstance(entity, Card):
            return False

        if not entity.is_generated:
            return False

        return entity.creator_base_identity == self.creator.base_identity

    def __repr__(self) -> str:
        return f"GENERATED_BY({self.creator!r})"


@dataclass(frozen=True, slots=True, eq=False)
class SpentGoldLastTurn(Predicate):
    spells_only: bool = False

    def test(self, entity: 'Player', ctx: 'ActionContext', **kwargs) -> bool:
        if not isinstance(entity, Player):
            return False

        if ctx.game.turn == 1:
            return False

        amount = 0
        for event in ctx.game.log:
            if isinstance(event, SpentGoldResult):
                if self.spells_only and not event.spent_on_spell:
                    continue

                amount += event.amount

        return amount > 0

    def __repr__(self) -> str:
        return "SPENT_GOLD_LAST_TURN"


IS_MONSTER = IsTypePredicate(CardType.MONSTER)
IS_SPELL = IsTypePredicate(CardType.SPELL)

DAMAGED = DamagedPredicate()

HAS_KEYWORD = lambda keyword: HasKeywordPredicate(keyword)
HAS_STATUS = lambda status_id: HasStatusPredicate(status_id)

GENERATED = GeneratedPredicate(True)
NON_GENERATED = GeneratedPredicate(False)

GENERATED_BY = lambda creator: GeneratedByPredicate(creator)

SPENT_GOLD_LAST_TURN = SpentGoldLastTurn()
SPENT_GOLD_LAST_TURN_ON_SPELLS = SpentGoldLastTurn(spells_only=True)


TOKEN = (RARITY == CardRarity.TOKEN)
NON_TOKEN = (RARITY < CardRarity.TOKEN)

DT = (RARITY == CardRarity.DETERMINATION)
NON_DT = (RARITY != CardRarity.DETERMINATION)
