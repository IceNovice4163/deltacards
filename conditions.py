from abc import ABC, abstractmethod
from functools import partial
from typing import TYPE_CHECKING

from entity import Entity
from player import Player

if TYPE_CHECKING:
    from game import Game
    from targeting import TargetSelector


__all__ = (
    'Condition',
    'SpentGoldLastTurn',
)


class Condition(ABC):
    @abstractmethod
    def eval(self, game: 'Game', caller: Entity, **kwargs) -> bool:
        pass


class SpentGoldLastTurn(Condition):
    def __init__(self, selector: 'TargetSelector', spells_only: bool = False):
        self.selector = selector
        self.spells_only = spells_only

    def eval(self, game: 'Game', **kwargs) -> bool:
        targets = self.selector.eval(game, **kwargs)
        assert len(targets) == 1

        target = targets[0]
        assert isinstance(target, Player)

        if game.turn == 1:
            return False

        return target.get_gold_spent(game.turn - 1, spells_only=self.spells_only) > 0


SpentGoldOnSpellsLastTurn = partial(SpentGoldLastTurn, spells_only=True)
