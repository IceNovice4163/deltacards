from typing import TYPE_CHECKING

from actions import *
from conditions import *
from cards import TargetsEnum, Monster, Spell, card, create_card
from targeting import *

if TYPE_CHECKING:
    from ..player import Player
    from ..game import Game


@card(3)
class Whimsun(Monster):
    def magic(self, game: 'Game', **kwargs):
        player = game.players[self.owner_id]
        return Buff(target=SELF, attack=len(player.board) - 1)


@card(5)
class Migosp(Monster):
    magic = Buff(target=ADJACENT(SELF), hp=1)


@card(6)
class Vegetoid(Monster):
    turn_start = Heal(target=OWNER, amount=5)


@card(10)
class Ice(Monster):
    dust = Paralyze(target=KILLER)


@card(11)
class Snowdrake(Monster):
    targets = TargetsEnum.ALLY_MONSTER,
    magic = Buff(target=TARGET, attack=2)


@card(13)
class Woshua(Monster):
    magic = Buff(target=ENEMY_MONSTERS, attack=-1)


@card(16)
class Madjick(Monster):
    targets = TargetsEnum.ALLY_MONSTER, TargetsEnum.ENEMY_MONSTER
    magic = SwapStats(TARGET)


@card(20)
class Vulkin(Monster):
    targets = TargetsEnum.YOU, TargetsEnum.OPPONENT, TargetsEnum.ALLY_MONSTER, TargetsEnum.ENEMY_MONSTER
    magic = Hit(target=TARGET, damage=2)


@card(22)
class Shyren(Monster):
    targets = TargetsEnum.YOU, TargetsEnum.OPPONENT, TargetsEnum.ALLY_MONSTER, TargetsEnum.ENEMY_MONSTER
    magic = Heal(target=TARGET, amount=4)


@card(44)
class Gyftrot(Monster):
    magic = DrawNext(target=OWNER)


@card(144)
class ScarfMouse(Monster):
    targets = TargetsEnum.ENEMY_MONSTER,
    magic = Silence(TARGET)


@card(147)
class FukuFire(Monster):
    magic = Hit(target=FRONT, damage=3)


@card(176)
class UglyFish(Monster):
    targets = TargetsEnum.ENEMY_MONSTER,
    magic = Send(target=TARGET, to='owner_hand')


@card(225)
class FishingRod(Monster):
    turn_end = DrawNext(target=OWNER)


@card(235)
class DadSlime(Monster):
    def dust(self, game: 'Game', **kwargs):
        return [
            Summon(target=create_card(370, creator_id=self.meta.fixed_id, owner_id=self.owner_id))
            for _ in range(2)
        ]


@card(72)
class Melt(Spell):
    targets = TargetsEnum.ALLY_MONSTER,
    magic = Hit(target=FRONT(TARGET), damage=TARGET.hp)


@card(76)
class Strength(Spell):
    magic = Buff(target=RANDOM(ALLY_MONSTERS, n=2), attack=1, hp=1)


@card(96)
class Punishment(Spell):
    targets = TargetsEnum.ENEMY_MONSTER,

    def magic(self, game: 'Game', **kwargs):
        damage = 4 if game.check(SpentGoldLastTurn(OWNER)) else 3
        return Hit(target=TARGET, damage=damage)


@card(132)
class Pie(Spell):
    targets = TargetsEnum.ALLY_MONSTER, TargetsEnum.ENEMY_MONSTER
    magic = Heal(target=TARGET, amount=TARGET.max_hp)
