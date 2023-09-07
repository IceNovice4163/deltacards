from typing import TYPE_CHECKING

from actions import *
from cards import Card, Monster, Spell, TargetsEnum, CardZone
from constants import GOLD_GAINS
from containers import CardContainer, Deck, Board
from entity import Entity
from targeting import SELF

if TYPE_CHECKING:
    from ai import AI
    from main import Game


class Player(Entity):
    def __init__(self, player_id: int, deck: Deck, is_first_turn: bool, ai: 'Type[AI] | None' = None):
        self.id = player_id
        self.deck = deck
        self.is_first_turn = is_first_turn
        self.ai = ai() if ai else None

        self.hand = CardContainer([])
        self.board = Board()
        self.dustpile = CardContainer([])
        self.gold = 1
        self.hp = 30
        self.max_hp = 30
        self.fatigue_counter = 0

        self.verbose = True
        self.game: Game | None = None
        self.opponent: Player | None = None

    def __str__(self):
        return f"Player {self.id}"

    def copy(self, **kwargs):  # TODO
        return Player(self.id, self.deck, is_first_turn=self.is_first_turn, ai=self.ai)

    def debug(self, msg: str) -> None:
        if self.verbose:
            tag = 'hp' if self.is_first_turn else 'atk'
            self.game.print(f"[{tag}][P{int(not self.is_first_turn) + 1}][/{tag}] {msg}")

    def print_state(self) -> None:
        self.game.print(f"[g]{self.gold}G[/g], {len(self.deck)} cards")

    def get_gold_spent(self, turn: int, spells_only: bool = False):
        return sum(
            -res.action.gold_change for res in self.game.log
            if res.turn == turn and res.player_id == self.id
                and isinstance(res.action, AffectsGold) and res.action.gold_change < 0
                and ((not spells_only) or isinstance(res.source, Spell))
        )

    def increase_gold(self, turn: int):
        try:
            self.gold += GOLD_GAINS[int(not self.is_first_turn)][turn - 1]
        except IndexError:
            self.gold += 10

    def draw(self, card_id: int) -> Card:
        card = self.deck.pop(card_id)

        if len(self.hand) < 7:
            card.zone = CardZone.HAND
            self.hand.add(card)

        else:
            card.zone = CardZone.BURNED
            self.debug(f"Discard {card} (overdraw)")

        return card

    def draw_next(self, count: int = 1) -> None:
        for _ in range(count):
            if len(self.deck) > 0:
                card = self.deck.cards[0]
                self.game.handle_actions(Draw(card=card), target=self, caller=self)

            else:
                self.fatigue_counter += 1
                self.debug(f"Fatigue! {self.fatigue_counter} damage")
                self.receive_damage(self.fatigue_counter)

    def get_target_choices(self, card: Card) -> list['Player | Card']:
        targets = []

        for target_type in card.targets:
            if target_type == TargetsEnum.YOU:
                targets.append(self)
            elif target_type == TargetsEnum.OPPONENT:
                targets.append(self.opponent)
            elif target_type == TargetsEnum.ALLY_MONSTER:
                targets += self.board.cards
            elif target_type == TargetsEnum.ENEMY_MONSTER:
                targets += self.opponent.board.cards
            elif target_type == TargetsEnum.HAND:
                targets += [c for c in self.hand.cards if c.id != card.id]
            elif target_type == TargetsEnum.DECK:
                targets += self.deck.cards

        return targets

    def play_card(self, card_id: int, pos: int | None = None, target = None):
        card = self.hand.get(card_id)
        if card.cost > self.gold:
            raise RuntimeError("Not enough [g]G[/g] to play card")

        self.hand.pop(card_id)
        self.gold -= card.cost
        if self.verbose:
            if target:
                self.debug(f"Target: {target}")

        card.owner_id = self.id

        self.game.handle_actions(Play(pos=pos), target=card, caller=self)
        self.game.handle_actions(card.magic, target=target, caller=card)

    def receive_damage(self, damage: int):
        self.hp -= damage
        if self.verbose:
            self.debug(f"HP left: {self.hp}")

    def heal(self, amount: int):
        self.hp = min(self.hp + amount, self.max_hp)

    def on_turn_start(self, turn: int) -> None:
        self.increase_gold(turn)
        if self.verbose:
            self.debug(f"Turn start, [g]{self.gold}G[/g]")
            self.debug(f"Hand: {self.hand}")

        self.game.handle_actions(DrawNext(target=SELF), caller=self)

        for monster in self.board.cards:
            monster.on_turn_start()

            if hasattr(monster, 'turn_start'):
                self.game.handle_actions(monster.turn_start, caller=monster)

    def on_turn_end(self, turn: int) -> None:
        self.debug("Turn end")
        for monster in self.board.cards:
            monster.on_turn_end()

            if hasattr(monster, 'turn_end'):
                self.game.handle_actions(monster.turn_end, caller=monster)

    def handle_turn(self) -> None:
        if self.ai:
            self.ai.handle_turn(self)


class ConsolePlayer(Player):
    def handle_command(self, text: str) -> None:
        sp = text.split()
        action, args = sp[0], sp[1:]

        if action in ('s', 'state'):
            self.print_state()

        elif action in ('b', 'board'):
            self.game.print_board()

        elif action in ('p', 'play'):
            card_id = int(args[0])
            try:
                card = self.hand.get(card_id)
            except StopIteration:
                self.game.print("Card not found")
                return

            if card.targets:
                choices = self.get_target_choices(card)
                if choices:
                    self.game.print(
                        f"{card}: select a target:\n" +
                        "\n".join(f"{i + 1}) {choice}" for i, choice in enumerate(choices)) +
                        "\n0) Cancel",
                    )
                    index = int(input()) - 1
                    if index == -1:
                        return

                    target = choices[index]

                else:
                    target = None

                self.play_card(card.id, target=target)

            else:
                self.play_card(card.id)

        if action in ('a', 'atk', 'attack'):
            self.game.attack(int(args[0]), int(args[1]))

    def handle_turn(self) -> None:
        while True:
            text = input()
            if not text:
                break

            self.handle_command(text)
