from typing import TYPE_CHECKING

from actions import *
from artifacts import Save
from entity import Entity, on_event
from enums import CardKeyword, CardZone, PlayerId
from targeting import *

if TYPE_CHECKING:
    from actions import ActionContext
    from player import Player

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

    game_start = None
    turn_start = None
    turn_end = None


@soul('empty_soul')
class EmptySoul(Soul):
    """Soul with no effects to simplify testing"""
    pass


@soul('kindness')
class Kindness(Soul):
    def turn_end(self, ctx: 'ActionContext'):
        if (ALLY_MONSTERS & DAMAGED).eval(ctx.game, self):
            yield Heal(target=ALLY_MONSTERS, amount=1)
        else:
            yield Buff(target=RIGHTMOST(ALLY_MONSTERS), hp=1)

        yield Heal(target=CONTROLLER, amount=1)


@soul('determination')
class Determination(Soul):
    def __init__(self, id: int, controller_id: PlayerId):
        super().__init__(id, controller_id)

        self.extra_life = True

    def game_start(self, ctx: 'ActionContext'):
        controller = self._get_controller(ctx)
        controller.next_lost_soul = 0
        return AddArtifact(target=CONTROLLER, artifact=Save(owner_id=self.controller_id.id))

    @on_event(Kill, pre=True)
    def on_kill(self, action: Kill, ctx: ActionContext):
        if self.extra_life and isinstance(action.target, Player) and action.target.id == self.owner_id:
            self.extra_life = False
            return SetPlayerHP(target=CONTROLLER, hp=5), True

        return None


@soul('patience')
class Patience(Soul):
    def turn_end(self, ctx: 'ActionContext'):
        controller = self._get_controller(ctx)
        if ctx.game.turn % 2 == 0 and len(controller.hand) < 7 and ((HAND | DECK) & (TEMPLATE_ID == 552)).eval(ctx=ctx):
            return Move(target=CARD_BY_NAME("ChangeOfWinds") >> GENERATE(), zone=CardZone.DECK, pos='top')

        return None


@soul('bravery')
class Bravery(Soul):
    def turn_start(self, ctx: 'ActionContext'):
        if ctx.game.turn % 3 == 0:
            controller = self._get_controller(ctx)
            if len(controller.hand) < 7:
                return Move(target=CARD_BY_NAME("Recruitment") >> GENERATE(), zone=CardZone.HAND)
            else:
                return Move(target=CARD_BY_NAME("Draft") >> GENERATE(), zone=CardZone.DECK, pos='top')

        return None


@soul('integrity')
class Integrity(Soul):
    def turn_end(self, ctx: 'ActionContext'):
        controller = self._get_controller(ctx)
        if ctx.game.turn > 1 and controller.get_gold_spent(ctx.game.turn) > controller.get_gold_spent(ctx.game.turn - 1):
            return EarnGold(target=CONTROLLER, amount=1)

        return None


@soul('perseverance')
class Perseverance(Soul):
    turn_start = AddKeyword(target=MAX(ENEMY_MONSTERS & ~HAS_KEYWORD(KR), TARGET.attack), keyword=CardKeyword.KR)


@soul('justice')
class Justice(Soul):
    def turn_end(self, ctx: 'ActionContext'):
        yield Hit(target=MIN(ENEMY_MONSTERS, TARGET.attack), damage=1)

        controller = self._get_controller(ctx)
        if controller.hp < controller.opponent.hp:
            yield Hit(target=OPPONENT, damage=1)
