from deltacards.actions.standard import *
from deltacards.model.entity import Entity
from deltacards.model.enums import PlayerId
from deltacards.model.snapshots import SoulSnapshot

SOULS = {}


def soul(soul_id):
    def wrapper(class_):
        if soul_id in SOULS:
            raise ValueError(f"Soul with ID {soul_id} already exists")

        SOULS[soul_id] = class_
        return class_

    return wrapper


class Soul(Entity):
    __slots__ = 'owner_id', 'controller_id'

    def __init__(self, id: int, controller_id: PlayerId):
        super().__init__(id)

        self.owner_id = controller_id
        self.controller_id = controller_id

    def __str__(self):
        return self.__class__.__name__

    def _get_controller(self, ctx: ActionContext):
        return ctx.game.player(self.controller_id)

    @property
    def base_identity(self) -> tuple[str, int]:
        return 'soul', [soul_id for soul_id, soul_cls in SOULS.items() if self.__class__ is soul_cls][0]

    def to_snapshot(self) -> SoulSnapshot:
        return SoulSnapshot(
            id=self.id,
            name=self.__class__.__name__,
            controller_id=self.controller_id,
        )
