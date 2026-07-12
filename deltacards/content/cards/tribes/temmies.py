from deltacards.dsl.api import *


TEMMIE = HAS_TRIBE(Tribe.TEMMIE)


@card(50)
class Temmie(Monster):
    magic = SELF.schedule_delay_effect()

    delay = GENERATE_CARD("Temmie 2").to_hand()


@card(139)
class TraderTemmie(Monster):
    turn_end = Check(COUNT(HAND) <= 5).to(
        DISCOVER(IS_SPELL, NON_TOKEN, COST <= 1).to_hand()
    )


@card(172)
class AllergicTemmie(Monster):
    magic = (SELF | ENEMY_MONSTERS).hit(
        COUNT(ALLY_MONSTERS & TEMMIE & ~SELF)
    )


@card(200)
class Bob(Monster):
    magic = (
        (
            DUSTPILE
            & TEMMIE
            & (TEMPLATE_ID != SELF.template_id)
        )
        >> DISTINCT(TEMPLATE_ID)
        >> SORT_BY(COST)
        >> COPY()
    ).to_hand()


@card(281)
class SchoolTem(Monster):
    draw_result: Var[StepResult] = Var(StepResult)

    magic = (
        YOU.draw(
            (DECK & TEMMIE).first()
        ).store_result(draw_result).to(
            Buff(target=draw_result.card_id, attack=+1, hp=+1),
            else_=(
                SELF.buff(attack=+1, hp=+1)
                >> SELF.add_keyword(HASTE)
            )
        )
    )


@card(785)
class TemmieEgg(Monster):
    magic = SELF.schedule_delay_effect()

    delay = GENERATE_CARD("Temmie 2").to_hand()

    dust = GENERATE_CARD("Temmie 2").to_hand()
