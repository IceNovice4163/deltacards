from deltacards.dsl.api import *


PLANT = HAS_TRIBE(Tribe.PLANT)


@card(746)
class SweetDance(Spell):
    magic = (ALLY_MONSTERS & PLANT).add_keyword(CANDY)


@card(747)
class MockingDance(Spell):
    magic = (ALLY_MONSTERS & PLANT).add_keyword(TAUNT)


@card(748)
class SwiftDance(Spell):
    magic = (ALLY_MONSTERS & PLANT).add_keyword(HASTE)


@card(749)
class FluidDance(Spell):
    magic = (ALLY_MONSTERS & PLANT).buff(hp=+2)
