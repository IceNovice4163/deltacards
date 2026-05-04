from enum import Enum
from typing import TYPE_CHECKING

from actions import *
from cards import Monster
from entity import Entity, on_event
from enums import CardKeyword, CardZone, PlayerId
from targeting import *

if TYPE_CHECKING:
    from player import Player

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
    __slots__ = 'owner_id', 'controller_id', 'counter', 'active'

    name: str
    rarity: ArtifactRarity
    initial_counter: int = 0

    def __init__(self, id: int, controller_id: PlayerId):
        super().__init__(id)

        self.owner_id = controller_id
        self.controller_id = controller_id

        self.counter = self.initial_counter
        self.active = True

    def __str__(self):
        return self.name

    def _get_controller(self, ctx: ActionContext) -> 'Player':
        return ctx.game.player(self.controller_id)

    @property
    def base_identity(self) -> tuple[str, int]:
        return 'artifact', [artifact_id for artifact_id, artifact_cls in ARTIFACTS.items() if self.__class__ is artifact_cls][0]

    game_start = None
    turn_start = None
    turn_end = None


@artifact(1)
class Health(Artifact):
    name = "Health"
    rarity = ArtifactRarity.BASE

    game_start = Buff(target=CONTROLLER, hp=5)


@artifact(2)
class Draw(Artifact):
    name = "Draw"
    rarity = ArtifactRarity.BASE

    game_start = DrawNext(player=CONTROLLER)

    def turn_start(self, ctx: 'ActionContext'):
        controller = self._get_controller(ctx)
        if ctx.game.turn % 6 == 0 and len(controller.hand) < 7:
            return DrawNext(player=CONTROLLER)

        return None


@artifact(3)
class Poke(Artifact):
    name = "Poke"
    rarity = ArtifactRarity.BASE

    game_start = Buff(target=OPPONENT, hp=-5)


@artifact(4)
class Power(Artifact):
    name = "Power"
    rarity = ArtifactRarity.BASE

    def turn_start(self, ctx: 'ActionContext'):
        if ctx.game.turn % 3 == 0:
            return Buff(target=RANDOM(HAND & IS_MONSTER), attack=1, hp=1)

        return None


@artifact(6)
class Solidity(Artifact):
    name = "Solidity"
    rarity = ArtifactRarity.BASE

    @on_event(Kill)
    def on_kill(self, ctx: 'ActionContext', target: 'Monster | Player', **kwargs):
        if isinstance(target, Monster) and target.controller_id == self.controller_id and target.has_keyword(CardKeyword.TAUNT):
            return Move(target=CARD_BY_NAME("Shield") >> GENERATE(), zone=CardZone.DECK, pos='top')

        return None


@artifact(11)
class Preservation(Artifact):
    name = "Preservation"
    rarity = ArtifactRarity.COMMON
    initial_counter = 7

    def on_would_overdraw(self, player: 'Player', **kwargs):
        if player.id == self.controller_id and self.counter >= 1:
            return UpdateArtifactCounter(artifact=self, delta=-1)

        return False


@artifact(33)
class Save(Artifact):
    name = "Save"
    rarity = ArtifactRarity.TOKEN

    def turn_end(self, ctx: 'ActionContext'):
        controller = self._get_controller(ctx)
        if self.counter >= 8:
            yield UpdateArtifactCounter(artifact=self, delta=-8)

            if len(controller.board) < controller.board.MAX_CARDS:
                yield Summon(target=CONTROLLER, card=NEXT_LOST_SOUL, attack=1, hp=1)
            else:
                yield TriggerAbility(target=NEXT_LOST_SOUL, ability=MAGIC)  # TODO

    @on_event(Kill)
    def on_kill(self, ctx: 'ActionContext', target: 'Monster | Player', **kwargs):
        if isinstance(target, Monster):
            return UpdateArtifactCounter(artifact=self, delta=1)

        return None
