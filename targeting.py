import operator
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from cards import Card, Monster, CardZone
from entity import Entity

if TYPE_CHECKING:
    from game import Game


__all__ = (
    'TargetSelector',
    'SELF', 'TARGET', 'KILLER', 'OWNER', 'OPPONENT',
    'FRONT', 'LEFT', 'RIGHT', 'ADJACENT',
    'BOARD', 'HAND', 'DECK', 'DUSTPILE',
    'ALLIES', 'ENEMIES',
)


class TargetSelector(ABC):
    def __add__(self, other: 'TargetSelector') -> 'OpSelector':
        return OpSelector(operator.add, self, other)

    def __sub__(self, other: 'TargetSelector') -> 'OpSelector':
        return OpSelector(operator.sub, self, other)

    @abstractmethod
    def eval(self, game: 'Game', caller: Entity, **kwargs) -> list[Entity]:
        pass


class OpSelector(TargetSelector):
    def __init__(self, op, var1: TargetSelector, var2: TargetSelector):
        self.op = op
        self.var1 = var1
        self.var2 = var2

    def eval(self, **kwargs) -> list[Entity]:
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
        targets = self.selector.eval(game, **kwargs)
        assert len(targets) == 1

        target = targets[0]
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

ALLIES = OWNER + BOARD()
ENEMIES = OPPONENT + BOARD(opponent=True)
