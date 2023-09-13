import math
import random
from typing import TYPE_CHECKING

from cards import Card, Monster, Spell, CardZone
from entity import Entity
from targeting import *

if TYPE_CHECKING:
    from player import Player
    from game import Game


__all__ = (
    'Action', 'AffectsGold', 'ActionResult',
    'Hit', 'Kill', 'Heal', 'Buff', 'SwapStats', 'HalveStats', 'Silence', 'Paralyze',
    'Draw', 'DrawNext', 'Summon', 'Play', 'Send', 'Attack', 'Earn',
    'AddCardToDeck',
)


class Action:
    def __init__(self, target: 'Targets | Entity', **kwargs):
        self.target = target

        self._args = kwargs
        self._args_cache = {}

    def __getattr__(self, name):
        if name in self._args:
            if name in self._args_cache:
                return self._args_cache[name]

            return self._args[name]

        raise AttributeError

    def __mul__(self, count: int):
        assert isinstance(count, int)
        return [self] * count

    def eval_args(self, **kwargs):
        for arg_name, arg in self._args.items():
            if hasattr(arg, 'eval'):
                value = arg.eval(**kwargs)
                self._args_cache[arg_name] = value

    def execute(self, *args, **kwargs):
        pass


class AffectsGold:
    def __init__(self):
        super().__init__()
        self.gold_change = 0


class ActionResult:
    def __init__(
        self,
        log: str | None = None,
        *,
        affected: list[Entity] | None = None,
        extra_actions: list[Action] | None = None,
    ):
        self.log = log
        self.affected = affected or []
        self.extra_actions = extra_actions or []

        self.action = None
        self.player_id = None
        self.source = None
        self.turn = None


class Hit(Action):
    def __init__(self, damage: int, target: 'Targets | Entity' = TARGET):
        super().__init__(target, damage=damage)

    def execute(self, target: 'Player | Monster', **kwargs):
        target.receive_damage(self.damage)
        return ActionResult(f"{target} received {self.damage} damage", affected=[target])


class Kill(Action):
    def __init__(self, target: 'TargetSelector | Entity' = TARGET):
        super().__init__(target)

    def execute(self, game: 'Game', target: 'Monster | Player', caller: Entity, **kwargs):
        game.kill(target, caller)
        return ActionResult(affected=[target])


class Heal(Action):
    def __init__(self, amount: int, target: 'TargetSelector | Entity' = TARGET):
        super().__init__(target, amount=amount)

    def execute(self, target: 'Player | Monster', **kwargs):
        hp_recovered = target.heal(self.amount)
        return ActionResult(f"{target} recovered {hp_recovered} HP", affected=[target])


class Buff(Action):
    def __init__(self, cost: int = 0, attack: int = 0, hp: int = 0, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target, cost=cost, attack=attack, hp=hp)

    def execute(self, target: 'Monster | Player', **kwargs):
        from player import Player  # TODO
        if isinstance(target, Monster):
            target.buff(self.cost, self.attack, self.hp)
        elif isinstance(target, Player):
            assert self.cost == 0 and self.attack == 0
            target.buff(hp=self.hp)

        return ActionResult(affected=[target])


class SwapStats(Action):
    def __init__(self, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target)

    def execute(self, target: Monster, **kwargs):
        target.buff(attack=target.hp - target.attack, hp=target.attack - target.hp)
        return ActionResult(affected=[target])


class HalveStats(Action):
    def __init__(self, round_up: bool, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target, round_up=round_up)

    def execute(self, target: Monster, **kwargs):
        round_func = math.floor if self.round_up else math.ceil  # negative stat buffs are inverted
        target.buff(attack=-round_func(target.attack / 2), hp=-round_func(target.hp / 2))

        return ActionResult(affected=[target])


class Silence(Action):
    def __init__(self, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target)

    def execute(self, target: Monster, **kwargs):
        target.silence()
        return ActionResult(affected=[target])


class Paralyze(Action):
    def __init__(self, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target)

    def execute(self, target: Monster, **kwargs):
        if isinstance(target, Monster):
            target.paralyze()
            return ActionResult(affected=[target])


class Draw(Action):
    def __init__(self, card: Card | SearchCard, target: 'TargetSelector | Card' = TARGET):
        super().__init__(target, card=card)

    def execute(self, target: 'Player', **kwargs):
        if not self.card:
            return

        card = target.draw(self.card.id)
        return ActionResult(f"Draw {card}")


class DrawNext(Action):
    def __init__(self, count: int = 1, target: 'TargetSelector | Player' = TARGET):
        super().__init__(target, count=count)

    def execute(self, target: 'Player', **kwargs):
        target.draw_next(self.count)


class Summon(Action):
    def __init__(self, pos: int | None = None, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target, pos=pos)

    def execute(self, game: 'Game', target: Monster, **kwargs):
        player = game.players[target.owner_id]
        if len(player.board) == player.board.MAX_CARDS:
            return

        if self.pos:
            pos = self.pos
            player.board[pos] = target
        else:
            pos = player.board.add(target)

        target.zone = CardZone.BOARD
        target.pos = pos


class Play(Summon, AffectsGold):
    def __init__(self, pos: int | None = None, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(pos, target)

    def execute(self, game: 'Game', target: Card, **kwargs):
        if isinstance(target, Monster):
            super().execute(game, target, **kwargs)

        if isinstance(target, Spell):
            target.zone = CardZone.DUSTPILE

        self.gold_change = -target.cost

        return ActionResult(f"Play {target}", affected=[target])


class Send(Action):
    def __init__(self, to: str, target: 'TargetSelector | Card' = TARGET):
        super().__init__(target, to=to)

    def execute(self, game: 'Game', target: 'Card', **kwargs):
        extra_actions = []
        if self.to == 'owner_hand':  # TODO
            owner = game.players[target.owner_id]

            if len(owner.hand) < 7:  # TODO constant
                owner.board[owner.board.get_card_index(target)] = None
                target.zone = CardZone.HAND
                owner.hand.add(target)

            else:
                extra_actions.append(Kill(target=target))

        return ActionResult(affected=[target], extra_actions=extra_actions)


class Attack(Action):
    def __init__(self, target: 'TargetSelector | Entity' = TARGET, attacker: 'TargetSelector | Entity' = SELF):
        super().__init__(target, attacker=attacker)

    def execute(self, game: 'Game', target: Monster, attacker: Monster | Spell, **kwargs):
        defender = target

        if isinstance(defender, Monster) and defender.zone != CardZone.BOARD:
            print(f"{defender} is not on board, attack cancelled")

        if attacker and isinstance(defender, Monster):
            attacker.receive_damage(defender.attack)

        defender.receive_damage(attacker.attack)

        return ActionResult(f"{attacker} attacked {defender}", affected=[defender, attacker])


class Earn(Action, AffectsGold):
    def __init__(self, amount: int, target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target, amount=amount)

    def execute(self, game: 'Game', target: Card, **kwargs):
        assert self.amount >= 0
        self.gold_change = self.amount

        return ActionResult(f"Earn {self.amount}G")


class AddCardToDeck(Action):
    def __init__(self, pos: str = 'random', target: 'TargetSelector | Monster' = TARGET):
        super().__init__(target, pos=pos)

    def execute(self, game: 'Game', target: Monster, **kwargs):
        player = game.players[target.owner_id]

        if self.pos == 'random':
            pos = random.randint(0, len(player.deck))
        elif self.pos == 'top':
            pos = 0
        elif self.pos == 'bottom':
            pos = None
        else:
            raise ValueError(f"Invalid position: {self.pos}")

        player.deck.add(target, pos=pos)
        target.zone = CardZone.DECK

        return ActionResult(affected=[target])
