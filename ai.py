from cards import Card, Monster, Spell, TargetsEnum
from game import Game
from player import Player


class AI:
    def handle_turn(self, player: Player) -> None:
        pass


class SimpleAI(AI):
    def find_target(self, cards: list[Monster], game: Game, attacker: Card, max_hp: bool) -> Monster | None:
        board_sorted = sorted(
            [i for i in cards if game.can_attack(attacker, i)],
            key=lambda card: (card.attack, card.hp if max_hp else -card.hp),
            reverse=True,
        )
        if not board_sorted:
            return

        return list(board_sorted)[0]

    def attack(self, player: Player) -> None:
        for card in player.board.cards:
            if not card:
                continue

            if card.can_attack in (1, 2):
                if len(player.opponent.board) == 0 and card.can_attack == 2:
                    target_id = player.opponent.id
                else:
                    target = self.find_target(player.opponent.board.cards, game=player.game, attacker=card, max_hp=False)
                    if not target:
                        continue

                    target_id = target.id

                player.game.attack(card.id, target_id)

    def handle_turn(self, player: Player) -> None:
        hand_sorted = sorted(player.hand.cards, key=lambda card: card.cost, reverse=True)
        for card in hand_sorted:
            if card.cost > player.gold:
                continue

            if isinstance(card, Monster):
                if len(player.board) < 4:
                    if card.targets:
                        if TargetsEnum.ALLY_MONSTER in card.targets:
                            target = self.find_target(player.board.cards, game=player.game, attacker=card, max_hp=True)
                        elif TargetsEnum.ENEMY_MONSTER in card.targets:
                            target = self.find_target(player.opponent.board.cards, game=player.game, attacker=card, max_hp=False)
                        elif TargetsEnum.OPPONENT in card.targets:
                            target = player.opponent
                        else:
                            target = None

                        if not target:
                            continue

                    else:
                        target = None

                    player.play_card(card.id, target=target)

            elif isinstance(card, Spell):
                target = self.find_target(player.opponent.board.cards, game=player.game, attacker=card, max_hp=False)
                if target:
                    player.play_card(card.id, target=target)

        self.attack(player)
