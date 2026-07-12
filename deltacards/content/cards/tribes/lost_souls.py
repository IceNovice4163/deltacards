from deltacards.dsl.api import *


LOST_SOUL = HAS_TRIBE(Tribe.LOST_SOUL)


@card(360)
class LostToriel(Monster):
    dust = (ENEMY_MONSTERS >> RANDOM(1)).buff(attack=-3)


@card(361)
class LostAsgore(Monster):
    dust = ((ENEMY_MONSTERS & DAMAGED) >> RANDOM(1)).hit(4)


@card(362)
class LostSans(Monster):
    dust = GENERATE_CARD("Gaster Blaster").to_hand()


@card(363)
class LostPapyrus(Monster):
    dust = (
        ((ALLY_MONSTERS & DAMAGED) >> RANDOM(1)).heal(3)
        >> YOU.heal(3)
    )


@card(364)
class LostUndyne(Monster):
    dust = (ENEMY_MONSTERS >> MIN(HP)).hit(2)


@card(365)
class LostAlphys(Monster):
    dust = (HAND >> MAX(COST)).buff(cost=-2)
