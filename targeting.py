import operator
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from cards import Card, Monster, CardZone
from entity import Entity

if TYPE_CHECKING:
    from game import Game


__all__ = (
    'LazyProperty', 'TargetSelector', 'SearchCards', 'SearchCard',
    'SELF', 'TARGET', 'KILLER', 'OWNER', 'OPPONENT',
    'FRONT', 'LEFT', 'RIGHT', 'ADJACENT',
    'BOARD', 'HAND', 'DECK', 'DUSTPILE',
    'ALLY_MONSTERS', 'ENEMY_MONSTERS', 'ALLIES', 'ENEMIES',
    'RANDOM',
    'ATTRIBUTE', 'NOATTRIBUTE',
)


class LazyProperty:
    def __init__(self, selector: 'TargetSelector', attr_name: str):
        self.selector = selector
        self.attr_name = attr_name

    def __eq__(self, other):
        return PropertyConstraint(operator.eq, self.attr_name, other)

    def __ne__(self, other):
        return PropertyConstraint(operator.ne, self.attr_name, other)

    def __lt__(self, other):
        return PropertyConstraint(operator.lt, self.attr_name, other)

    def __le__(self, other):
        return PropertyConstraint(operator.le, self.attr_name, other)

    def __ge__(self, other):
        return PropertyConstraint(operator.ge, self.attr_name, other)

    def __gt__(self, other):
        return PropertyConstraint(operator.gt, self.attr_name, other)

    def eval(self, game: 'Game', **kwargs) -> int:
        target = self.selector.eval_single(game, **kwargs)
        assert isinstance(target, Entity)

        return getattr(target, self.attr_name)


class TargetSelector(ABC):
    def __add__(self, other: 'TargetSelector') -> 'OpSelector':
        return OpSelector(operator.add, self, other)

    def __sub__(self, other: 'TargetSelector') -> 'OpSelector':
        return OpSelector(operator.sub, self, other)

    def __getattr__(self, name):
        if name in ('cost', 'attack', 'hp', 'max_hp', 'loop', 'pos'):
            return LazyProperty(self, name)

        raise AttributeError

    @abstractmethod
    def eval(self, game: 'Game', caller: Entity, **kwargs) -> list[Entity]:
        pass

    def eval_single(self, game: 'Game', caller: Entity, **kwargs):
        targets = self.eval(game, caller, **kwargs)
        assert len(targets) == 1

        return targets[0]


class OpSelector(TargetSelector):
    def __init__(self, op, var1: 'TargetSelector | AttributeConstraint | LazyProperty', var2: TargetSelector):
        self.op = op
        self.var1 = var1
        self.var2 = var2

    def eval(self, **kwargs) -> list[Entity]:
        if self.op == operator.and_:
            assert isinstance(self.var1, TargetSelector)
            assert isinstance(self.var2, AttributeConstraint)
            result = self.var2.eval(entities=self.var1.eval(**kwargs))

        elif self.op in (operator.eq, operator.ne, operator.lt, operator.le, operator.ge, operator.gt):
            return self.op(
                self.var1.eval(**kwargs) if isinstance(self.var1, LazyProperty) else self.var1,
                self.var2.eval(**kwargs) if isinstance(self.var2, LazyProperty) else self.var2,
            )

        else:
            result = self.op(
                self.var1.eval(**kwargs),
                self.var2.eval(**kwargs),
            )

        return list(set(result))


class FunctionSelector(TargetSelector):
    def __init__(self, function: Callable):
        self.function = function

    def eval(self, game: 'Game', caller: Card, **kwargs) -> list[Entity]:
        result = self.function(caller=caller, game=game, **kwargs)
        if not isinstance(result, list):
            result = [result]

        return result


class BoardSelector(TargetSelector):
    def __init__(self, selector: TargetSelector, x: int = 0, opposite: bool = False):
        self.selector = selector
        self.x = x
        self.opposite = opposite

    def eval(self, game: 'Game', **kwargs) -> list[Entity]:
        target = self.selector.eval_single(game, **kwargs)
        assert isinstance(target, Monster)

        pos = target.pos + self.x
        player = game.players[target.owner_id]
        if self.opposite:
            player = player.opponent

        board = player.board
        if 0 <= pos < board.MAX_CARDS and board[pos]:
            return [board[pos]]

        return []


class ZoneSelector(TargetSelector):
    def __init__(self, zone: CardZone, opponent: bool = False):
        assert zone in (CardZone.BOARD, CardZone.HAND, CardZone.DECK, CardZone.DUSTPILE)

        self.zone = zone
        self.opponent = opponent

    def eval(self, game: 'Game', caller: Card, **kwargs) -> list[Card]:
        player = game.players[caller.owner_id]
        if self.opponent:
            player = player.opponent

        return getattr(player, self.zone.value).cards


class RandomSelector(TargetSelector):
    def __init__(self, selector: TargetSelector, n: int = 1):
        self.selector = selector
        self.n = n

    def eval(self, game: 'Game', **kwargs) -> list[Entity]:
        return random.sample(self.selector.eval(game, **kwargs), k=self.n)


class PropertyConstraint(TargetSelector):
    def __init__(self, op, attr_name: str, value: int):
        self.op = op
        self.attr_name = attr_name
        self.value = value

    def eval(self, entities: list[Card], **kwargs) -> list[Entity]:
        return list(filter(
            lambda card: self.op(getattr(card, self.attr_name), self.value),
            entities,
        ))


class AttributeConstraint(TargetSelector):
    def __init__(self, attr_name: str, check_if_true: bool = True):
        self.attr_name = attr_name
        self.check_if_true = check_if_true

    def __rand__(self, other):
        return OpSelector(operator.and_, other, self)

    def eval(self, entities: list[Monster], **kwargs) -> list[Entity]:
        return list(filter(
            lambda m: getattr(m.attributes, self.attr_name) ^ (not self.check_if_true),
            entities,
        ))


class SearchCards(TargetSelector):
    def __init__(self, selector: TargetSelector, *args, n: int = 1):
        self.selector = selector
        self.constraints = args
        self.n = n

    def eval(self, **kwargs) -> list[Entity]:
        result = self.selector.eval(**kwargs)
        for constraint in self.constraints:
            result = constraint.eval(entities=result)

        return result[:self.n]


class SearchCard(TargetSelector):
    def __init__(self, selector: TargetSelector, *args):
        self.selector = selector
        self.constraints = args

    def eval(self, **kwargs) -> Entity:
        return next(iter(
            SearchCards(self.selector, *self.constraints).eval(**kwargs)
        ), None)


SELF = FunctionSelector(lambda caller, **kwargs: caller)
TARGET = FunctionSelector(lambda caller, **kwargs: kwargs.get('target'))
KILLER = FunctionSelector(lambda caller, **kwargs: kwargs.get('killer'))
OWNER = FunctionSelector(lambda caller, game, **kwargs: game.players[caller.owner_id])
OPPONENT = FunctionSelector(lambda caller, game, **kwargs: game.players[caller.owner_id].opponent)

FRONT = lambda target: BoardSelector(target, opposite=True)
LEFT = lambda target: BoardSelector(target, x=-1)
RIGHT = lambda target: BoardSelector(target, x=1)
ADJACENT = lambda target: LEFT(target) + RIGHT(target)

BOARD = lambda opponent=False: ZoneSelector(CardZone.BOARD, opponent)
HAND = lambda opponent=False: ZoneSelector(CardZone.HAND, opponent)
DECK = lambda opponent=False: ZoneSelector(CardZone.DECK, opponent)
DUSTPILE = lambda opponent=False: ZoneSelector(CardZone.DUSTPILE, opponent)

ALLY_MONSTERS = BOARD()
ENEMY_MONSTERS = BOARD(opponent=True)
ALLIES = OWNER + ALLY_MONSTERS
ENEMIES = OPPONENT + ENEMY_MONSTERS

RANDOM = RandomSelector

ATTRIBUTE = AttributeConstraint
NOATTRIBUTE = lambda attr_name: AttributeConstraint(attr_name, check_if_true=False)
