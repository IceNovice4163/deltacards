from typing import TYPE_CHECKING

from actions import *
from cards import TargetsEnum, Monster, Spell, card, create_card

if TYPE_CHECKING:
    from ..player import Player
    from ..game import Game


@card(3)
class Whimsun(Monster):
    def magic(self, game: 'Game', **kwargs):
        player = game.players[self.owner_id]
        return Buff(target=Targets.SELF, attack=len(player.board) - 1)


@card(5)
class Migosp(Monster):
    magic = Buff(target=Targets.ADJACENT, hp=1)


@card(6)
class Vegetoid(Monster):
    turn_start = Heal(target=Targets.PLAYER, amount=5)


@card(10)
class Ice(Monster):
    dust = Paralyze(target=Targets.KILLER)


@card(11)
class Snowdrake(Monster):
    targets = TargetsEnum.ALLY_MONSTER,
    magic = Buff(target=Targets.TARGET, attack=2)


@card(13)
class Woshua(Monster):
    magic = Buff(target=Targets.ENEMY_MONSTERS, attack=-1)


@card(16)
class Madjick(Monster):
    targets = TargetsEnum.ALLY_MONSTER, TargetsEnum.ENEMY_MONSTER
    magic = SwapStats(Targets.TARGET)


@card(20)
class Vulkin(Monster):
    targets = TargetsEnum.YOU, TargetsEnum.OPPONENT, TargetsEnum.ALLY_MONSTER, TargetsEnum.ENEMY_MONSTER
    magic = Hit(target=Targets.TARGET, damage=2)


@card(22)
class Shyren(Monster):
    targets = TargetsEnum.YOU, TargetsEnum.OPPONENT, TargetsEnum.ALLY_MONSTER, TargetsEnum.ENEMY_MONSTER
    magic = Heal(target=Targets.TARGET, amount=4)


@card(44)
class Gyftrot(Monster):
    magic = DrawNext(target=Targets.PLAYER)


@card(144)
class ScarfMouse(Monster):
    targets = TargetsEnum.ENEMY_MONSTER,
    magic = Silence(Targets.TARGET)


@card(147)
class FukuFire(Monster):
    magic = Hit(target=Targets.FRONT, damage=3)


@card(176)
class UglyFish(Monster):
    targets = TargetsEnum.ENEMY_MONSTER,
    magic = Send(target=Targets.TARGET, to='owner_hand')


@card(225)
class FishingRod(Monster):
    turn_end = DrawNext(target=Targets.PLAYER)


@card(235)
class DadSlime(Monster):
    def dust(self, game: 'Game', **kwargs):
        return [
            Summon(target=create_card(370, creator_id=self.meta.fixed_id, owner_id=self.owner_id))
            for _ in range(2)
        ]


@card(96)
class Punishment(Spell):
    targets = TargetsEnum.ENEMY_MONSTER,

    def magic(self, game: 'Game', **kwargs):
        return Hit(target=Targets.TARGET, damage=3)
