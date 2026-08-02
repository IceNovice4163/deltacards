from deltacards.dsl.api import *


@card(391)
class Sheary(Monster):
    targets = ALL_MONSTERS

    magic = Check(TARGET & DAMAGED).to(
        TARGET.hit(4),
        else_=TARGET.hit(1)
    )


@card(396)
class Hathy(Monster):
    support = ATTACKER.buff(attack=+1)


@card(650)
class WalkSign(Monster):
    targets = ALL_MONSTERS

    magic = (
        TARGET.hit(3)
        >> YOU.hit(3)
    )


@card(788)
class RalseiDummy(Monster):
    shock = (
        SELF.buff(hp=+2)
        >> SELF.toggle_ability(SHOCK, False)
    )
