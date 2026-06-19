from typing import TYPE_CHECKING

from deltacards.dsl.api import *
from deltacards.model.artifacts import Artifact, ArtifactRarity, artifact

if TYPE_CHECKING:
    from deltacards.engine.game import Game


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
                yield TriggerAbility(target=NEXT_LOST_SOUL, ability=DUST)

    @on_event(MonsterKilledResult)
    def on_monster_killed(self, res: MonsterKilledResult, game: Game, **kwargs):
        return UpdateArtifactCounter(artifact=self, delta=1)
