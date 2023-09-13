import itertools
from contextvars import ContextVar
from typing import Callable

from rich import box
from rich.console import Console
from rich.table import Table, Column
from rich.theme import Theme

from actions import *
from conditions import *
from cards import Monster, Card, CardZone, Spell
from entity import Entity
from player import Player
from targeting import TargetSelector


action_caller: ContextVar[Entity] = ContextVar('action_caller')


class GameOver(Exception):
    pass


class Game:
    def __init__(self, players: tuple[Player, Player]):
        self.players: dict[int, Player] = {player.id: player for player in players}
        for player in players:
            player.game = self
            player.opponent = next(other for other in players if other.id != player.id)

        self.turn = 1
        self.verbose = True
        self.log: list[ActionResult] = []

        custom_theme = Theme({
            'g': 'bold yellow',
            'atk': 'bold red',
            'atk-paralyzed': 'bold',
            'hp': 'bold green',
            'hp-low': 'bold yellow',
            'monster': 'bold bright_magenta',
            'spell': 'bold cyan',
            'warn': 'bold orange3',
            'error': 'bold red',
        })
        self._console = Console(theme=custom_theme)

    def print(self, *objects):
        self._console.print(*objects)

    def get_me(self):
        return self.players[1]

    def print_game_state(self):
        self.print(f"Turn {self.turn}")
        self.get_me().print_state()

    def locate(self, card_id: int) -> Monster:
        card = None
        for player in self.players.values():
            try:
                card = player.board.get(card_id)
            except StopIteration:
                pass
            else:
                break

        if not card:
            raise ValueError(f"Card {card_id} not found")

        return card

    def can_attack(self, attacker: Card, defender: Player | Monster) -> bool:
        if isinstance(attacker, Spell):  # TODO
            return True

        if isinstance(defender, Player):
            defender_board = defender.board
        elif isinstance(defender, Monster):
            defender_board = self.players[defender.owner_id].board
        else:
            raise TypeError(f"Defender is of invalid type {type(defender)}")

        if isinstance(defender, Monster) and defender.attributes.taunt:
            return True

        for monster in defender_board.cards:
            if monster.attributes.taunt:
                return False

        return True

    def attack(self, attacker_id: int, defender_id: int, is_spell: bool = False):
        if is_spell:
            attacker = None
        else:
            attacker = self.locate(attacker_id)

        if defender_id in self.players:
            defender = self.players[defender_id]
        else:
            defender = self.locate(defender_id)

        if not self.can_attack(attacker, defender):
            raise ValueError(f"{attacker} is unable to attack {defender}")

        self.handle_actions(Attack(), caller=attacker, target=defender, attacker=attacker)

    def kill(self, target: Monster | Player, killer: Entity):
        if isinstance(target, Monster):
            self.players[target.owner_id].board.pop(target.id)
            target.zone = CardZone.DUSTPILE

            if hasattr(target, 'dust'):
                self.handle_actions(target.dust, caller=target, killer=killer)

        elif isinstance(target, Player):
            target.debug(f"{target} defeated")
            raise GameOver

        else:
            raise TypeError(f"Target is of invalid type {type(target)}")

        if self.verbose:
            self.print(f"{target} was killed")

    def check(self, condition: Condition) -> bool:
        return condition.eval(game=self, caller=action_caller.get())

    def _call_event_handlers(self, pre: bool, action: Action, caller: Entity, **kwargs) -> bool:
        should_cancel_event = False
        for entity in itertools.chain(
            (artifact for player in self.players.values() for artifact in player.artifacts),
            (monster for player in self.players.values() for monster in player.board.cards),
        ):
            if entity is caller:
                continue

            event_handlers = entity.pre_event_handlers if pre else entity.post_event_handlers
            for action_class, event_handler in event_handlers.items():
                if isinstance(action, action_class):
                    if self.handle_actions(
                        actions=event_handler(entity, game=self, caller=caller, **kwargs),
                        caller=caller,
                        **kwargs,
                    ):
                        should_cancel_event = True

        return should_cancel_event

    def handle_action(
        self,
        action: Action,
        caller: Entity,
        original_target: Entity,
        **kwargs,
    ):
        if isinstance(action.target, Entity):
            targets = [action.target]
        elif isinstance(action.target, TargetSelector):
            targets = action.target.eval(game=self, target=original_target, caller=caller, **kwargs)
        else:
            raise TypeError(f"Action target is of invalid type {action.target}")

        for i in targets:
            action.eval_args(game=self, target=original_target, caller=caller, **kwargs)
            should_cancel_event = self._call_event_handlers(pre=True, action=action, target=i, caller=caller, **kwargs)
            if should_cancel_event:
                continue

            res = action.execute(game=self, target=i, caller=caller, **kwargs)
            if not res:
                res = ActionResult()

            self.log.append(res)

            if res.log:
                if isinstance(caller, Player):
                    caller.debug(res.log)
                elif self.verbose:
                    self.print(res.log)

            self._call_event_handlers(pre=False, action=action, target=i, caller=caller, **kwargs)

            for entity in res.affected:
                if (not isinstance(entity, Spell)) and entity.hp <= 0\
                        and (isinstance(entity, Player) or entity.zone == CardZone.BOARD)\
                        and not isinstance(action, Kill):
                    self.handle_actions(Kill(), target=entity, caller=caller)

            for extra_action in res.extra_actions:
                self.handle_actions(extra_action, caller=caller)

            res.affected = [entity.copy(exact=True, assign_new_id=False) for entity in res.affected]
            res.action = action
            res.player_id = caller.id if isinstance(caller, Player) else caller.owner_id
            res.source = caller
            res.turn = self.turn

    def handle_actions(
        self,
        actions: Action | list[Action] | Callable,
        caller: Entity,
        **kwargs,
    ) -> bool | None:
        token = action_caller.set(caller)
        if isinstance(actions, Callable):
            actions = actions(game=self, caller=caller, **kwargs)

        if not actions:
            return

        if isinstance(actions, Action):
            actions = [actions]
        elif isinstance(actions, bool):
            return actions

        original_target = kwargs.pop('target', None)

        should_cancel_event = False
        for action in actions:
            if isinstance(action, Action):
                self.handle_action(action, caller, original_target, **kwargs)
            elif isinstance(action, bool):
                should_cancel_event = action

        action_caller.reset(token)
        return should_cancel_event

    def start_turn(self, player: Player):
        player.on_turn_start(self.turn)

    def end_turn(self, player: Player):
        player.on_turn_end(self.turn)
        if list(self.players.values())[-1] == player:
            if self.verbose:
                self.print(f"End of turn {self.turn}")

            self.turn += 1

    def turn_loop(self):
        for player in self.players.values():
            self.start_turn(player)
            self.print_board()
            player.handle_turn()
            self.end_turn(player)

    def run(self):
        for player in self.players.values():
            player.draw_next(3)

        for player in self.players.values():
            player.on_game_start()

        while True:
            self.turn_loop()

    def print_board(self):
        if not self.verbose:
            return

        width = 20
        board = []
        for player in self.players.values():
            player_board = []
            for monster in player.board._cards:
                if not monster:
                    player_board.append(' ' * width)
                    continue

                player_board.append(monster.to_str())

            board.append(player_board)

        table = Table(
            Column(min_width=20), Column(min_width=20), Column(min_width=20), Column(min_width=20),
            show_header=False, show_lines=True, box=box.SQUARE,
        )
        table.add_row(*board[1])
        table.add_row(*board[0])
        self.print(table)
