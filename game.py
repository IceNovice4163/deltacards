from typing import Callable

from rich import box
from rich.console import Console
from rich.table import Table, Column
from rich.theme import Theme

from actions import *
from cards import Monster, Card, CardZone, Spell
from entity import Entity
from player import Player
from targeting import TargetSelector


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
        self.log = []

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

    def handle_actions(
        self,
        actions: Action | list[Action] | Callable,
        caller: Entity,
        **kwargs,
    ):
        if isinstance(actions, Callable):
            actions = actions(game=self, caller=caller, **kwargs)

        if not actions:
            return

        if isinstance(actions, Action):
            actions = [actions]

        for action in actions:
            if isinstance(action.target, Entity):
                targets = [action.target]
            elif isinstance(action.target, TargetSelector):
                targets = action.target.eval(game=self, caller=caller, **kwargs)
            else:
                raise TypeError(f"Action target is of invalid type {action.target}")

            kwargs.pop('target', None)

            for i in targets:
                res = action.execute(game=self, target=i, caller=caller, **kwargs)
                if res:
                    if res.log:
                        self.log.append(f"{res.log}, caller: {caller}")
                        if isinstance(caller, Player):
                            caller.debug(res.log)
                        else:
                            self.print(res.log)

                    for entity in res.affected:
                        if entity.hp <= 0\
                                and (isinstance(entity, Player) or entity.zone == CardZone.BOARD)\
                                and not isinstance(action, Kill):
                            self.handle_actions(Kill(), target=entity, caller=caller)

                    for extra_action in res.extra_actions:
                        self.handle_actions(extra_action, caller=caller)

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
