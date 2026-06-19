from typing import TYPE_CHECKING

from deltacards.dsl.api import *
from deltacards.model.artifacts import Artifact, ArtifactRarity, artifact

if TYPE_CHECKING:
    from deltacards.model.player import Player


@artifact(11)
class Preservation(Artifact):
    name = "Preservation"
    rarity = ArtifactRarity.COMMON
    initial_counter = 7

    def on_would_overdraw(self, player: 'Player', **kwargs):
        if player.id == self.controller_id and self.counter >= 1:
            return UpdateArtifactCounter(artifact=self, delta=-1)

        return False
