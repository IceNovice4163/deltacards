from cards import load
from enums import PlayerId
from game import Game
from player import Player

DECK = {
    'soul': 'PATIENCE',
    'cardIds': [
        235, 737, 465, 133, 133, 133, 71, 71, 71, 260,
        260, 457, 457, 182, 289, 289, 75, 465, 861, 861,
        861, 843, 843, 688, 791,
    ],
    'artifactIds': [2, 3],
}


def build_demo_game() -> Game:
    load()

    player1 = Player(
        PlayerId.P1,
        deck=DECK['cardIds'],
        soul_id=DECK['soul'],
        artifact_ids=DECK['artifactIds'],
        is_first_turn=True,
    )
    player2 = Player(
        PlayerId.P2,
        deck=DECK['cardIds'],
        soul_id=DECK['soul'],
        artifact_ids=DECK['artifactIds'],
        is_first_turn=False,
    )

    game = Game((player1, player2))
    return game
