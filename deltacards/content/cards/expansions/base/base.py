from deltacards.dsl.api import *


@card(3)
class Whimsun(Monster):
    magic = SELF.buff(attack=COUNT(ALLY_MONSTERS & ~SELF))


@card(5)
class Migosp(Monster):
    magic = ADJACENT(SELF).buff(hp=+1)


@card(10)
class Ice(Monster):
    dust = KILLER.paralyze()


@card(11)
class Snowdrake(Monster):
    targets = ALLY_MONSTERS

    magic = TARGET.buff(attack=+2)


@card(13)
class Woshua(Monster):
    magic = ENEMY_MONSTERS.buff(attack=-1)


@card(16)
class Madjick(Monster):
    targets = ALL_MONSTERS

    magic = TARGET.swap_stats()


@card(20)
class Vulkin(Monster):
    targets = ALL_PLAYERS | ALL_MONSTERS

    magic = TARGET.hit(2)


@card(22)
class Shyren(Monster):
    targets = ALL_PLAYERS | ALL_MONSTERS

    magic = TARGET.heal(4)


@card(44)
class Gyftrot(Monster):
    magic = DrawUpTo(2)


@card(144)
class ScarfMouse(Monster):
    targets = ENEMY_MONSTERS

    magic = TARGET.silence()


@card(147)
class FukuFire(Monster):
    magic = FRONT(SELF).hit(3)


@card(176)
class UglyFish(Monster):
    targets = ENEMY_MONSTERS

    magic = TARGET.to_hand()


@card(225)
class FishingRod(Monster):
    turn_end = YOU.draw_next()


@card(235)
class DadSlime(Monster):
    dust = GENERATE_CARD("Kid Slime").summon() * 2
