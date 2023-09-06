import enum
from typing import TYPE_CHECKING

from cards import Card, Monster, Spell, CardZone
from entity import Entity

if TYPE_CHECKING:
    from player import Player
    from game import Game


__all__ = (
    'Targets', 'Action', 'Action',
    'Hit', 'Kill', 'Heal', 'Buff', 'SwapStats', 'Silence', 'Paralyze',
    'Draw', 'DrawNext', 'Summon', 'Play', 'Send', 'Attack',
)


class Targets(str, enum.Enum):
    SELF = 'self'
    TARGET = 'target'
    KILLER = 'killer'
    ADJACENT = 'adjacent'
    PLAYER = 'player'
    FRONT = 'front'
    ALLY_MONSTERS = 'ally_monsters'
    ENEMY_MONSTERS = 'enemy_monsters'
    ENEMY_HAND = 'enemy_hand'


class Action:
    def __init__(self, target: 'Targets | Entity'):
        self.target = target

    def execute(self, *args, **kwargs):
        pass


class AffectsGold:
    def __init__(self):
        super().__init__()
        self.gold_change = 0


class ActionResult:
    def __init__(self, log: str | None = None, *, affected: list | None = None, extra_actions: list | None = None):
        self.log = log
        self.affected = affected or []
        self.extra_actions = extra_actions or []


class Hit(Action):
    def __init__(self, damage: int, target: 'Targets | Entity' = Targets.TARGET):
        super().__init__(target)
        self.damage = damage

    def execute(self, target: 'Player | Monster', **kwargs):
        target.receive_damage(self.damage)
        return ActionResult(affected=[target])


class Kill(Action):
    def __init__(self, target: 'Targets | Entity' = Targets.TARGET):
        super().__init__(target)

    def execute(self, game: 'Game', target: Monster, caller: Entity, **kwargs):
        game.kill(target, caller)
        return ActionResult(affected=[target])


class Heal(Action):
    def __init__(self, amount: int, target: 'Targets | Entity' = Targets.TARGET):
        super().__init__(target)
        self.amount = amount

    def execute(self, target: 'Player | Monster', **kwargs):
        target.heal(self.amount)
        return ActionResult(f"{target} recovered {self.amount} HP", affected=[target])


class Buff(Action):
    def __init__(self, cost: int = 0, attack: int = 0, hp: int = 0, target: 'Targets | Monster' = Targets.TARGET):
        super().__init__(target)
        self.cost = cost
        self.attack = attack
        self.hp = hp

    def execute(self, target: Monster, **kwargs):
        target.buff(self.cost, self.attack, self.hp)
        return ActionResult(affected=[target])


class SwapStats(Action):
    def __init__(self, target: 'Targets | Monster' = Targets.TARGET):
        super().__init__(target)

    def execute(self, target: Monster, **kwargs):
        target.buff(attack=target.hp - target.attack, hp=target.attack - target.hp)
        return ActionResult(affected=[target])


class Silence(Action):
    def __init__(self, target: 'Targets | Monster' = Targets.TARGET):
        super().__init__(target)

    def execute(self, target: Monster, **kwargs):
        target.silence()
        return ActionResult(affected=[target])


class Paralyze(Action):
    def __init__(self, target: 'Targets | Monster' = Targets.TARGET):
        super().__init__(target)

    def execute(self, target: Monster, **kwargs):
        if isinstance(target, Monster):
            target.paralyze()
            return ActionResult(affected=[target])


class Draw(Action):
    def __init__(self, card: Card, target: 'Targets | Card' = Targets.TARGET):
        super().__init__(target)
        self.card = card

    def execute(self, target: 'Player', **kwargs):
        card = target.draw(self.card.id)
        return ActionResult(f"Draw {card}")


class DrawNext(Action):
    def __init__(self, count: int = 1, target: 'Targets | Card' = Targets.TARGET):
        super().__init__(target)
        self.count = count

    def execute(self, target: 'Player', **kwargs):
        target.draw_next(self.count)


class Summon(Action):
    def __init__(self, pos: int | None = None, target: 'Targets | Monster' = Targets.TARGET):
        super().__init__(target)
        self.pos = pos

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

        return ActionResult(f"Play {target}", affected=[target])


class Play(Summon, AffectsGold):
    def __init__(self, pos: int | None = None, target: 'Targets | Monster' = Targets.TARGET):
        super().__init__(pos, target)

    def execute(self, game: 'Game', target: Monster, **kwargs):
        result = super().execute(game, target, **kwargs)
        self.gold_change = -result.affected[0].cost

        return result


class Send(Action):
    def __init__(self, to: str, target: 'Targets | Card' = Targets.TARGET):
        super().__init__(target)
        self.to = to

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
    def __init__(self, target: 'Targets | Entity' = Targets.TARGET, attacker: 'Targets | Entity' = Targets.SELF):
        super().__init__(target)
        self.attacker = attacker

    def execute(self, game: 'Game', target: Monster, attacker: Monster | Spell, **kwargs):
        defender = target

        if isinstance(defender, Monster) and defender.zone != CardZone.BOARD:
            print(f"{defender} is not on board, attack cancelled")

        if attacker and isinstance(defender, Monster):
            attacker.receive_damage(defender.attack)

        defender.receive_damage(attacker.attack)

        return ActionResult(f"{attacker} attacked {defender}", affected=[defender, attacker])
