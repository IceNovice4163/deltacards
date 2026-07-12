from deltacards.dsl.api import *


@card(796)
class GigaPunch(Spell):
    targets = ALLY_MONSTERS

    magic = (
        TARGET.set_status(DODGE, value=TARGET.status(DODGE) + 1)
        >> TARGET.force_attack((ENEMY_MONSTERS >> MIN(ATTACK)).first())
    )


@card(797)
class GigaMissiles(Spell):
    magic = ENEMIES.hit(3)


@card(798)
class GigaGlass(Spell):
    targets = ENEMY_MONSTERS

    magic = TARGET.kill()


@card(799)
class GigaBalls(Spell):
    magic = GENERATE_CARD("GIGA Baseball").summon() * 2
