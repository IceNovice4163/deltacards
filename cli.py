import colorama
from rich import box
from rich.console import Console, Group
from rich.progress_bar import ProgressBar
from rich.table import Column, Table
from rich.theme import Theme

from cards import Monster
from demo_game import build_demo_game
from enums import PlayerId
from runner import GameRunner
from schemas.requests import (
    Attack,
    ChooseEntityPrompt,
    EndTurn,
    PlayMonster,
    PlaySpell,
    ChoiceResponse,
    MulliganResponse,
    PendingChoiceRequest,
    PendingMulliganRequest,
    PendingPlayerActionRequest,
    PlayerActionResponse,
)


class CLIRunner:
    def __init__(self, runner: GameRunner):
        self.runner = runner
        self.game = self.runner.game

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

            'rarity-base': '#808080',
            'rarity-rare': '#00b8ff',
            'rarity-epic': '#d535d9',
            'rarity-legendary': '#ffd700',
            'rarity-determination': '#ff0000',
            'rarity-token': '#00c800',

            'soul-kindness': '#00c000',
            'soul-determination': '#ff0000',
            'soul-patience': '#41fcff',
            'soul-bravery': '#fca500',
            'soul-integrity': '#0064ff',
            'soul-perseverance': '#d535d9',
            'soul-justice': '#ffff00',
        })
        self._console = Console(theme=custom_theme, width=200)

    def print(self, *objects):
        self._console.print(*objects)

    def print_board(self):
        width = 20
        board = []

        turn_player_id = self.game.turn_player.id
        players = (self.game.player(turn_player_id), self.game.player(turn_player_id).opponent)

        for player in players:
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

        player_tables = []
        for player in players:
            player_table = Table(
                Column(width=1), Column(width=1), Column(width=1, justify='right'),
                expand=True, show_header=False, show_lines=True, box=box.HORIZONTALS,
            )
            player_table.add_row(
                f"[soul-{str(player.soul).lower()}]{player}[/soul-{str(player.soul).lower()}] [bright_black]"
                f"{' '.join(artifact.__class__.__name__ + (('[' + str(artifact.counter) + ']') if artifact.counter > 0 else '') for artifact in player.artifacts)}[/bright_black]",
                Group(
                    ProgressBar(completed=player.hp / player.max_hp * 100, width=10),
                    f" {player.hp}/{player.max_hp} [hp]HP[/hp]",
                ),
                Group(
                    (f"T: {self.game.turn}  " if player == players[-1] else "") + f"D: {len(player.deck)}  H: {len(player.hand)}  [g]G[/g]: {player.gold}",
                )
            )
            player_tables.append(player_table)

        container = Table(Column(), padding=(0, 0), show_header=False, show_edge=False)
        container.add_row(player_tables[1])
        container.add_row(table)
        container.add_row(player_tables[0])

        self.print(container)
        self.print(f"Hand: {players[0].hand}")

    def handle_command(self, request_id: int, player_id: PlayerId, text: str) -> None:
        sp = text.split()
        if not text:
            return

        cmd, args = sp[0], sp[1:]

        if cmd in ('s', 'state'):
            for player in self.game.players.values():
                self.print(
                    f"[P{player.id.value}]: [g]{player.gold}G[/g],"
                    f"{player.hp} / {player.max_hp} {player.hp}/{player.max_hp} [hp]HP[/hp]"
                )

        elif cmd in ('b', 'board'):
            self.print_board()

        elif cmd in ('d', 'deck'):
            self.print(str(self.game.player(player_id).deck))

        elif cmd in ('p', 'play'):
            if len(args) < 1:
                self.print("Usage: play <card_id> [slot]")

            player = self.game.player(player_id)
            card_id = int(args[0])
            try:
                card = player.hand.get(card_id)
            except StopIteration:
                self.print("Card not found")
                return

            if isinstance(card, Monster):
                if len(args) < 2:
                    try:
                        slot = player.board.get_empty_slot_index()
                    except StopIteration:
                        self.print("Board is full")
                        return

                else:
                    try:
                        slot = int(args[1]) - 1
                    except ValueError:
                        self.print("Slot must be a number from 1 to 4.")
                        return

                action = PlayMonster(card_id=card.id, board_slot=slot)

            else:
                action = PlaySpell(card_id=card.id)

            response = PlayerActionResponse(request_id=request_id, player_id=player_id, action=action)
            ok, reason = self.runner.provide_input(response)
            if not ok:
                self.print(f"Rejected: {reason}")

        elif cmd in ('a', 'attack'):
            if len(args) < 2:
                self.print("Usage: attack <attacker_id> <defender_id>")

            attacker_id = int(args[0])
            defender_id = int(args[1])

            action = Attack(attacker_id=attacker_id, defender_id=defender_id)
            response = PlayerActionResponse(request_id=request_id, player_id=player_id, action=action)
            ok, reason = self.runner.provide_input(response)
            if not ok:
                self.print(f"Rejected: {reason}")

        elif cmd == 'end':
            resp = PlayerActionResponse(
                request_id=request_id,
                player_id=player_id,
                action=EndTurn(),
            )
            ok, reason = self.runner.provide_input(resp)
            if not ok:
                self.print(f"Rejected: {reason}")

        else:
            self.print("Unknown command")

    def run(self) -> None:
        last_player_action_request_id = None
        while not self.game.game_over:
            upd = self.runner.resolve_until_blocked()
            for r in upd.results:
                self.print(r)

            if upd.game_over:
                self.print(f"Game over. Winner: Player {self.game.winner_id().value}")
                break

            req = upd.pending[0]

            if isinstance(req, PendingMulliganRequest):
                self.print(f"[P{req.player_id.value}] Mulligan:")
                for i, card_id in enumerate(req.prompt.offered_card_ids):
                    self.print(f"  {i + 1}: {self.game.entities[card_id]}")

                replace_ids_str = input(f"Choose cards to mulligan (e.g. '1 3'): ")
                try:
                    response = MulliganResponse(
                        request_id=req.request_id,
                        player_id=req.player_id,
                        replace_card_ids=tuple(req.prompt.offered_card_ids[int(i) - 1] for i in replace_ids_str.split()),
                    )
                except IndexError:
                    continue

                ok, reason = self.runner.provide_input(response)
                if not ok:
                    self.print(f"Rejected: {reason}")

            if isinstance(req, PendingPlayerActionRequest):
                if req.request_id != last_player_action_request_id:
                    last_player_action_request_id = req.request_id
                    self.print_board()

                self.handle_command(req.request_id, req.player_id, input())

            if isinstance(req, PendingChoiceRequest):
                prompt = req.prompt
                assert isinstance(prompt, ChooseEntityPrompt)

                self.print(
                    f"[P{req.player_id.value}] Choose a target:\n" +
                    "\n".join(f"{i + 1}) {choice}" for i, choice in enumerate(prompt.options))
                )
                index = int(input()) - 1
                if not 0 <= index < len(prompt.options):
                    self.print(f"Invalid index")
                    continue

                resp = ChoiceResponse(
                    request_id=req.request_id,
                    player_id=req.player_id,
                    selected_option_ids=(prompt.options[index].id,),
                )
                ok, reason = self.runner.provide_input(resp)
                if not ok:
                    self.print(f"Rejected: {reason}")

            continue


def main() -> None:
    colorama.just_fix_windows_console()

    game = build_demo_game()
    runner = GameRunner(game)
    CLIRunner(runner).run()


if __name__ == '__main__':
    main()
