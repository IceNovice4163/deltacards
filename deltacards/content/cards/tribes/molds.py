from deltacards.dsl.api import *


MOLD = HAS_TRIBE(Tribe.MOLD)


@card(19)
class Moldbygg(Monster):
    released_card: Var[Card] = Var(Card)

    magic = Check(ALLY_MONSTERS & MOLD).to(
        SELF.catch(GENERATE_CARD("Moldsmal"))
    )

    dust = SELF.release_caught_card(var=released_card).to(
        released_card.summon(controller=released_card.controller)
    )


@card(37)
class Moldessa(Monster):
    draw_result: Var[StepResult] = Var(StepResult)

    _effect = (
        YOU.draw(
            (DECK & MOLD & (TEMPLATE_ID != SELF.template_id)).first()
        ).store_result(draw_result).to(
            Buff(target=draw_result.card_id, attack=+1)
        )
    )

    magic = _effect
    dust = _effect


@card(491)
class Moldstack(Monster):
    magic = SELF.schedule_delay_effect()

    delay = (
        (ALLY_MONSTERS & MOLD & (TEMPLATE_ID != SELF.template_id))
        >> RANDOM(1)
        >> COPY()
    ).to_hand()


@card(590)
class Moldmega(Monster):
    summon_result: Var[StepResult] = Var(StepResult)

    _effect = Check(COUNT(DUSTPILE & MOLD) >= 5).to(
        (DUSTPILE & MOLD)[:5].erase()
        >> GENERATE_CARD("Moldbygg").summon().store_result(summon_result).to(
            TriggerAbility(target=summon_result.monster_id, ability=MAGIC)
        )
    )

    magic = _effect
    dust = _effect
