from deltacards.dsl.api import *


@card(818)
class TheFirstRound(Spell):
    targets = ENEMIES

    magic = TARGET.hit(1)

    bullseye = GENERATE_CARD("The Second Round").to_hand()


@card(819)
class TheSecondRound(Spell):
    targets = ENEMIES

    magic = TARGET.hit(2)

    bullseye = GENERATE_CARD("The Third Round").to_hand()


@card(820)
class TheThirdRound(Spell):
    targets = ENEMIES

    magic = TARGET.hit(3)

    bullseye = GENERATE_CARD("The Fourth Round").to_hand()


@card(821)
class TheFourthRound(Spell):
    targets = ENEMIES

    magic = TARGET.hit(4)

    bullseye = GENERATE_CARD("The Fifth Round").to_hand()


@card(822)
class TheFifthRound(Spell):
    targets = ENEMIES

    magic = TARGET.hit(5)

    bullseye = GENERATE_CARD("The Final Round").to_hand()


@card(823)
class TheFinalRound(Spell):
    magic = (
        ENEMIES.hit(6)
        >> Check(BOARD & (TEMPLATE_NAME == "Clover")).to(
            GENERATE_CARD("The First Round").to_hand()
        )
    )
