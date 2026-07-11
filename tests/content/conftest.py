from deltacards.dsl.api import *


@card(129)
class Knife(Spell):
    # Kill a monster. Deal its COST as DMG to you.
    targets = ALLY_MONSTERS | ENEMY_MONSTERS

    kill_result: Var[StepResult] = Var(StepResult)

    magic = (
        TARGET.kill().store_result(kill_result).to(
            YOU.hit(kill_result.monster.cost)
        )
    )


@card(71)
class FrozenEnergy(Spell):
    # Give a monster +2/+2 and HASTE. Delay: If its COST is the same as its base COST, Paralyze it.
    targets = ALL_MONSTERS

    magic = (
        TARGET.buff(attack=+2, hp=+2)
        >> TARGET.add_keyword(HASTE)
        >> SELF.schedule_delay_effect()
    )

    delay = Check(TARGET.cost == TARGET.base.cost).to(TARGET.paralyze())


@card(288)
class Pippins(Monster):
    # Turbo: If you have 6 or less cards in your hand, draw a card.
    turbo = Check(COUNT(HAND) <= 6).to(
        YOU.draw_next()
    )
