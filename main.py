import colorama

from ai import SimpleAI
from artifacts import ARTIFACTS
from cards import Monster, Spell, load
from containers import Deck
from game import Game, GameOver
from player import Player, ConsolePlayer


DECK = {
    'soul': 'JUSTICE',
    'cardIds': [115,115,115,225,225,225,9,9,9,96,96,96,144,144,20,20,20,15,15,15,235,235,235,44,44],
    'artifactIds':[2, 3],
}


def main():
    colorama.just_fix_windows_console()

    load()

    player1 = ConsolePlayer(
        1,
        Deck(DECK['cardIds'], shuffle=True),
        artifacts=[ARTIFACTS[artifact](owner_id=1) for artifact in DECK['artifactIds']],
        is_first_turn=True,
    )
    player2 = Player(
        2,
        Deck(DECK['cardIds'], shuffle=True),
        artifacts=[ARTIFACTS[artifact](owner_id=2) for artifact in DECK['artifactIds']],
        is_first_turn=False,
        ai=SimpleAI,
    )

    # for card in player1.deck.cards:
    #     if type(card) in (Monster, Spell):
    #         print(f'Unknown card with id {card.meta.fixed_id} ({card.meta.name})')

    game = Game((player1, player2))

    game.print_game_state()
    try:
        game.run()
    except GameOver:
        print('Game ended')


if __name__ == '__main__':
    main()
