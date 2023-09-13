from enum import Enum
from typing import TYPE_CHECKING

from actions import *
from cards import create_card
from entity import Entity, on_event
from targeting import *

if TYPE_CHECKING:
    from player import Player
    from game import Game

ARTIFACTS = {}


def artifact(artifact_id):
    def wrapper(class_):
        if artifact_id in ARTIFACTS:
            raise ValueError(f"Artifact with ID {artifact_id} already exists")

        ARTIFACTS[artifact_id] = class_
        return class_

    return wrapper


class ArtifactRarity(Enum):
    BASE = 'base'
    COMMON = 'common'
    LEGENDARY = 'legendary'
    TOKEN = 'token'


class Artifact(Entity):
    __slots__ = 'owner_id', 'counter', 'active'

    name: str
    rarity: ArtifactRarity

    def __init__(self, owner_id: int):
        super().__init__()

        self.owner_id = owner_id

        self.counter = 0
        self.active = True

    def __str__(self):
        return self.name

    def copy(self, **kwargs):
        return self

    def game_start(self, game: 'Game', caller: 'Artifact', owner: 'Player'):
        pass

    def turn_start(self, game: 'Game', caller: 'Artifact', owner: 'Player'):
        pass

    def turn_end(self, game: 'Game', caller: 'Artifact', owner: 'Player'):
        pass


@artifact(1)
class Health(Artifact):
    name = "Health"
    rarity = ArtifactRarity.BASE

    game_start = Buff(target=OWNER, hp=5)


@artifact(2)
class Draw(Artifact):
    name = "Draw"
    rarity = ArtifactRarity.BASE

    game_start = DrawNext(target=OWNER)

    def turn_start(self, game: 'Game', caller: 'Artifact', owner: 'Player'):
        if game.turn % 6 == 0 and len(owner.hand) < 7:
            return DrawNext(target=OWNER)


@artifact(3)
class Poke(Artifact):
    name = "Poke"
    rarity = ArtifactRarity.BASE

    game_start = Buff(target=OPPONENT, hp=-5)


@artifact(4)
class Power(Artifact):
    name = "Power"
    rarity = ArtifactRarity.BASE

    def turn_start(self, game: 'Game', caller: 'Artifact', owner: 'Player'):
        if game.turn % 3 == 0:
            return Buff(target=RANDOM(HAND() & IS_MONSTER), attack=1, hp=1)


@artifact(6)
class Solidity(Artifact):
    name = "Solidity"
    rarity = ArtifactRarity.BASE

    @on_event(Kill)
    def on_kill(self, game: 'Game', target: 'Monster | Player', caller: 'Entity', **kwargs):
        if target.owner_id == self.owner_id and target.attributes.taunt:
            return AddCardToDeck(target=create_card(576, creator_id=self.id, owner_id=self.owner_id), pos='top')
