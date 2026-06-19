from deltacards.dsl.api import *


@card(133)
class Fridge(Spell):
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = AddKeyword(target=TARGET, keyword=CardKeyword.TAUNT) >> DrawNext(player=CONTROLLER)


@card(71)
class FrozenEnergy(Spell):
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = (
        Buff(target=TARGET, attack=+2, hp=+2)
        >> AddKeyword(target=TARGET, keyword=CardKeyword.HASTE)
    ).to(
        ScheduleDelayEffect(SELF)
    )
    delay = Check(TARGET.cost == TARGET.base.cost).to(Paralyze(target=TARGET))


@card(260)
class IceReplica(Spell):
    targets = (ALLY_MONSTERS | ENEMY_MONSTERS) & NON_DT

    card: Var[Card] = Var(Card)

    magic = (
        Paralyze(target=TARGET)
        >> SetVar(var=card, value=TARGET.copy())
        >> Move(target=card, zone=CardZone.HAND)
        >> ScheduleDelayEffect(SELF)
    )
    delay = Check(card.controller == YOU).to(Buff(target=card, cost=-2))


@card(737)
class IceShock(Spell):
    res: Var[StepResult] = Var(StepResult)

    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Hit(target=TARGET, damage=2).store_result(res) >> Check((res.success == True) & (res.killed == True)).to(
        Paralyze(target=ADJACENT(res.target))
    )


@card(182)
class IcePrison(Spell):
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Silence(target=TARGET) >> Paralyze(target=TARGET)
