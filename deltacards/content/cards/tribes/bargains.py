from deltacards.dsl.api import *


@card(720)
class ClickHereToDie(Spell):
    target_monster: Var[Card] = Var(Card)
    excess_hp_lost: Var[int] = Var(int, default=6)

    magic = Check(ALLY_MONSTERS).to(
        SetVar(
            var=target_monster,
            value=(ALLY_MONSTERS >> MAX(HP)).first()
        )
        >> SetVar(
            var=excess_hp_lost,
            value=GREATEST(6 - target_monster.hp, 0)
        )
        >> target_monster.buff(hp=-6)
    ) >> Check(excess_hp_lost > 0).to(
        YOU.hit(excess_hp_lost)
    )


@card(721)
class PressF1ForHelp(Spell):
    magic = OPPONENT.buff(hp=+8)


@card(722)
class Generosity(Spell):
    magic = (
        YOU.spend_gold(6, allow_partial=True)
        >> OPPONENT.earn_gold(6)
    )


@card(723)
class Hotsingle(Spell):
    summon_result: Var[StepResult] = Var(StepResult)

    magic = SELF.schedule_delay_effect()

    delay = (
        GENERATE_CARD("Ms Pipis").summon().store_result(summon_result)
        >> Check(summon_result.success == False).to(
            ((ALLY_MONSTERS >> RANDOM(1)).turn_into(GENERATE_CARD("Ms Pipis")))
        )
    )
