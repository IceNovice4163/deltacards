from typing import TYPE_CHECKING

from deltacards.dsl.api import *
from deltacards.model.artifacts import Artifact, ArtifactRarity, artifact

if TYPE_CHECKING:
    from deltacards.engine.game import Game


@artifact(39)
class Reverberation(Artifact):
    name = "Reverberation"
    rarity = ArtifactRarity.LEGENDARY

    @on_event(MonsterSummonedResult)
    def on_monster_summoned(self, res: MonsterSummonedResult, game: 'Game', **kwargs):
        if not res.is_played:
            return None

        monster = game.entity(res.monster_id)
        if monster.controller_id != self.controller_id:
            return None

        if not monster.has_ability(Ability.TURBO):
            return None

        return TriggerAbility(target=monster, ability=Ability.TURBO)
