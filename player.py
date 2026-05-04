from typing import Any, Sequence, TYPE_CHECKING

from constants import GOLD_GAINS
from containers import Board, CardContainer, Deck
from entity import Entity
from enums import PlayerId
from snapshots import PlayerSnapshot

if TYPE_CHECKING:
    from artifacts import Artifact
    from game import Game
    from souls import Soul


class Player(Entity):
    def __init__(
        self,
        player_id: PlayerId,
        deck: Sequence[int],
        soul_id: str,
        artifact_ids: Sequence[int],
        is_first_turn: bool,
    ):
        self.id = player_id

        self.starting_deck_card_ids = deck
        self.starting_soul_id = soul_id.lower()
        self.starting_artifact_ids = artifact_ids
        self.is_first_turn = is_first_turn

        self.soul: 'Soul' = None
        self.artifacts: list['Artifact'] = None

        self.board = Board()
        self.hand = CardContainer()
        self.deck: Deck = None
        self.dustpile = CardContainer()
        self.erased = CardContainer()

        self.turn = 0
        self.gold = 10
        self.hp = 30
        self.max_hp = 30
        self.fatigue_counter = 0

        self.game: 'Game' = None
        self.opponent: 'Player' = None

    def __str__(self):
        return f"Player {self.id}"

    @property
    def controller_id(self) -> PlayerId:
        return self.id

    def increase_gold(self, turn: int) -> None:
        try:
            self.gold += GOLD_GAINS[int(not self.is_first_turn)][turn - 1]
        except IndexError:
            self.gold += 10

    def heal(self, amount: int) -> int:
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)

        return self.hp - old_hp

    def set_hp(self, hp: int) -> None:
        self.hp = hp
        if self.hp > self.max_hp:
            self.max_hp = hp

    def set_max_hp(self, hp: int) -> None:
        self.max_hp = hp
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def buff(self, hp: int = 0) -> None:
        self.hp += hp
        self.max_hp += hp

    def get_snapshot_attrs(self) -> dict:
        return dict(
            id=self.id,
            gold=self.gold,
            hp=self.hp,
            max_hp=self.max_hp,
        )

    def to_snapshot(self) -> 'PlayerSnapshot':
        return PlayerSnapshot(**self.get_snapshot_attrs())

    def serialize(self) -> dict[str, Any]:  # TODO
        return {
            'id': self.id,
            'hp': self.hp,
            'max_hp': self.max_hp,
        }
