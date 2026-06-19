from typing import TYPE_CHECKING

from deltacards.dsl.api import *
from deltacards.model.artifacts import Artifact, ArtifactRarity, artifact

if TYPE_CHECKING:
    from deltacards.engine.game import Game


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

    @on_event(MonsterKilledResult)
    def on_monster_killed(self, res: MonsterKilledResult, game: Game, **kwargs):
        if res.monster.controller_id == self.controller_id and res.monster.has_keyword(CardKeyword.TAUNT):
            return Move(target=CARD_BY_NAME("Shield") >> GENERATE(), zone=CardZone.DECK, pos='top')

        return None
