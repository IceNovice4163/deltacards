from deltacards.content.artifacts.token import Save
from deltacards.dsl.api import *
from deltacards.model.souls import Soul, soul


@soul('empty_soul')
class EmptySoul(Soul):
    """Soul with no effects to simplify testing"""
    pass


@soul('kindness')
class Kindness(Soul):
    def turn_end(self, ctx: 'ActionContext'):
        if ctx.game.turn < 3:
            return

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
        return AddArtifact(target=CONTROLLER, artifact=Save(controller_id=self.controller_id))

    def on_would_die(self, entity: Entity, **kwargs):
        if entity.id == self.controller_id and self.extra_life:
            self.extra_life = False
            return SetPlayerHP(player=entity, hp=5)

        return None


@soul('patience')
class Patience(Soul):
    def turn_end(self, ctx: 'ActionContext'):
        controller = self._get_controller(ctx)
        if ctx.game.turn % 2 == 0 and len(controller.hand) < 7 and not ((HAND | DECK) & (TEMPLATE_ID == 552)).eval(ctx=ctx):
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
                return Move(target=CARD_BY_NAME("Draft") >> GENERATE(), zone=CardZone.DECK)

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
    turn_start = AddKeyword(target=(ENEMY_MONSTERS & ~HAS_KEYWORD(KR)) >> MAX(ATTACK), keyword=CardKeyword.KR)


@soul('justice')
class Justice(Soul):
    turn_start = Hit(target=ENEMY_MONSTERS >> MIN(HP), damage=1)
