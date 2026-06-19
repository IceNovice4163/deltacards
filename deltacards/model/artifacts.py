from enum import Enum
from typing import TYPE_CHECKING

from deltacards.actions.standard import *
from deltacards.model.entity import Entity
from deltacards.model.enums import PlayerId

if TYPE_CHECKING:
    from deltacards.model.player import Player

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
        return (
            'artifact',
            [artifact_id for artifact_id, artifact_cls in ARTIFACTS.items() if self.__class__ is artifact_cls][0],
        )
