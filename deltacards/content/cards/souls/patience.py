from deltacards.dsl.api import *


@card(71)
class FrozenEnergy(Spell):
    targets = ALL_MONSTERS

    magic = (
        TARGET.buff(attack=+2, hp=+2)
        >> TARGET.add_keyword(HASTE)
        >> SELF.schedule_delay_effect()
    )

    delay = TARGET.paralyze()


@card(72)
class Melt(Spell):
    targets = ALLY_MONSTERS

    magic = FRONT(TARGET).hit(TARGET.hp)


@card(73)
class ColdWinter(Spell):
    hit_result: Var[StepResult] = Var(StepResult)
    kill_count: Var[int] = Var(int, default=0)

    magic = For(
        5,
        effect=(
            (ENEMY_MONSTERS >> RANDOM(1)).hit(1).store_result(hit_result).to(
                Check(hit_result.killed).to(
                    SetVar(var=kill_count, value=kill_count + 1)
                )
            )
        )
    ) >> For(
        kill_count,
        effect=GENERATE_CARD("Change of Winds").to_hand()
    )


@card(74)
class Defrosting(Spell):
    dog: Var[Card] = Var(Monster)

    magic = (
        Check(SELF & ~HAS_STATUS(LOOP)).to(
            SetVar(var=dog, value=GENERATE_CARD("Greater Dog"))
            >> dog.set_status(DODGE, value=1)
            >> dog.add_keyword(HASTE)
            >> dog.summon(attack=8, hp=5)
        )
        >> Program(2)
    )


@card(75)
class SelfReflection(Spell):
    targets = ALL_MONSTERS

    was_ally: Var[bool] = Var(bool, default=False)

    magic = (
        SetVar(var=was_ally, value=TARGET.controller_id == YOU.id)
        >> TARGET.paralyze()
        >> SELF.schedule_delay_effect()
    )

    delay = Check(was_ally).to(
        TARGET.add_keyword(CANDY)
        >> TARGET.buff(attack=+1, hp=+1),
        else_=GENERATE_CARD("True Self").to_hand()
    )


@card(133)
class Fridge(Spell):
    targets = ALL_MONSTERS

    magic = (
        TARGET.buff(hp=+1)
        >> TARGET.add_keyword(TAUNT)
        >> YOU.draw_next()
    )


@card(182)
class IcePrison(Spell):
    targets = ALL_MONSTERS

    magic = (
        TARGET.silence()
        >> TARGET.paralyze()
    )


@card(260)
class IceReplica(Spell):
    targets = ALL_MONSTERS & NON_DT

    generated_card: Var[Card] = Var(Monster)
    was_ally: Var[bool] = Var(bool, default=False)

    magic = (
        SetVar(var=was_ally, value=TARGET.controller_id == YOU.id)
        >> TARGET.paralyze()
        >> SetVar(var=generated_card, value=TARGET >> COPY())
        >> generated_card.to_hand()
        >> SELF.schedule_delay_effect()
    )

    delay = Check(was_ally).to(
        generated_card.buff(cost=-2)
    )


@card(457)
class Exploration(Spell):
    magic = YOU.draw_next(from_pos='bottom') * 2


@card(485)
class RoyalPatience(Spell):
    magic = YOU.choose(DECK).to(
        YOU.draw(CHOICE_SELECTED)
    )


@card(551)
class TrueSelf(Spell):
    targets = ALL_MONSTERS

    magic = (
        TARGET.kill()
        >> (ENEMY_MONSTERS & HAS_STATUS(PARALYZED)).kill()
    )


@card(552)
class ChangeOfWinds(Spell):
    magic = YOU.choose(DECK[:2]).to(
        YOU.draw(CHOICE_SELECTED)
        >> CHOICE_NOT_SELECTED.to_deck(pos='bottom')
        >> (CHOICE_SELECTED | CHOICE_NOT_SELECTED).buff(cost=-1)
    )


@card(698)
class SnowWarning(Spell):
    magic = (
        YOU.add_artifact(ARTIFACT_BY_NAME("Hail"))
        >> YOU.artifact("Hail").update_artifact_counter(+4)
        >> ALL_MONSTERS.hit(1)
    )


@card(737)
class IceShock(Spell):
    targets = ALL_MONSTERS

    hit_result: Var[StepResult] = Var(StepResult)
    adjacent_monsters: Var[TargetSelector] = Var(TargetSelector)

    magic = (
        SetVar(var=adjacent_monsters, value=ADJACENT(TARGET))
        >> TARGET.hit(2).store_result(hit_result).to(
            Check(hit_result.killed).to(
                adjacent_monsters.paralyze()
            )
        )
    )


@card(861)
class Oasis(Spell):
    spell_count: Var[int] = Var(int)

    magic = (
        For(3, effect=GENERATE_CARD("Change of Winds").to_hand())
        >> SELF.schedule_delay_effect()
    )

    delay = (
        SetVar(
            var=spell_count,
            value=COUNT(HAND & (TEMPLATE_NAME == "Change of Winds"))
        )
        >> (HAND & (TEMPLATE_NAME == "Change of Winds")).erase().to(
            YOU.heal(spell_count * 3)
        )
    )
