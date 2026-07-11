from deltacards.dsl.api import *

from ..rig import TestRig


@card(26)
class Parsnik(Monster):
    # Magic: Paralyze a monster. If it was already Paralyzed, deal 2 DMG to it.
    paralyze_result: Var[StepResult] = Var(StepResult)

    targets = ALL_MONSTERS

    magic = (
        TARGET.paralyze().store_result(paralyze_result)
        >> Check(paralyze_result.success == False).to(
            TARGET.hit(2)
        )
    )


def test_card_parsnik():
    rig = TestRig.create(p1_deck=[1, 26, 26])

    dummy = rig.p1.hand[0]
    parsnik = rig.p1.hand[1]
    parsnik_2 = rig.p1.hand[2]

    rig.p1.play_monster(dummy, slot=0)
    rig.p1.play_monster(parsnik, slot=1, target=dummy)

    assert dummy.get_status(CardStatusId.PARALYZED) == 2
    assert dummy.hp == dummy.base.hp

    rig.p1.end_turn()
    rig.p2.end_turn()

    assert dummy.get_status(CardStatusId.PARALYZED) == 1

    rig.p1.play_monster(parsnik_2, slot=2, target=dummy)

    assert dummy.get_status(CardStatusId.PARALYZED) == 1
    assert dummy.hp == dummy.base.hp - 2


@card(73)
class ColdWinter(Spell):
    # Deal 11 DMG randomly split among all enemy monsters. Add a Change Of Winds to your hand for each one that died.
    hit_result: Var[StepResult] = Var(StepResult)
    kill_count: Var[int] = Var(int, default=0)

    magic = For(
        11,
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


def test_card_coldwinter():
    rig = TestRig.create(p1_deck=[1, 1, 1], p2_deck=[73])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

    rig.p1.end_turn()

    rig.p2.play_spell(rig.p2.hand[0])
    # Only one of monsters that were on the board must survive, and that monster must have exactly 1 HP left
    assert sum(1 for m in rig.p1.board if m) == 1
    assert next(m for m in rig.p1.board if m).hp == 1
    assert [c.template.id for c in rig.p2.hand] == [1, 1, 1, 552, 552]


@card(737)
class IceShock(Spell):
    # Deal 2 DMG to a monster. If it kills, Paralyze the adjacent ones.
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


def test_card_iceshock():
    rig = TestRig.create(p1_deck=[1, 1, 1], p2_deck=[737])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

    monster = rig.p1.board[1]
    monster.hp_missing = monster.hp - 1

    rig.p1.end_turn()

    rig.p2.play_spell(rig.p2.hand[0], target=monster)
    assert rig.p1.board[1] is None
    assert isinstance(rig.p1.board[0], Monster)
    assert isinstance(rig.p1.board[2], Monster)
    assert rig.p1.board[0].get_status(CardStatusId.PARALYZED) == 2
    assert rig.p1.board[2].get_status(CardStatusId.PARALYZED) == 2


@card(62)
class Undyne(Monster):
    # Deal 1 DMG to the lowest HP enemy monster 10 times. Summon a Spear with base stats equal to DMG not dealt.
    damage_not_dealt: Var[int] = Var(int, default=0)

    magic = For(
        10,
        effect=Check(COUNT(ENEMY_MONSTERS) > 0).to(
            (ENEMY_MONSTERS >> MIN(HP)).hit(1),
            else_=SetVar(
                var=damage_not_dealt,
                value=damage_not_dealt + 1,
            )
        )
    ) >> Check(damage_not_dealt > 0).to(
        GENERATE_CARD("Spear").summon(
            attack=damage_not_dealt,
            hp=damage_not_dealt,
        )
    )


def test_card_undyne():
    rig = TestRig.create(p1_deck=[1, 1], p2_deck=[62])

    for _ in range(2):
        rig.p1.play_monster(rig.p1.hand[0])

    rig.p1.end_turn()

    rig.p2.play_monster(rig.p2.hand[0])

    assert sum(1 for m in rig.p1.board if m) == 0
    assert [m.template.name for m in rig.p2.board if m] == ["Undyne", "Spear"]
    assert rig.p2.board[1].attack == rig.p2.board[1].base.attack == 2
    assert rig.p2.board[1].hp == rig.p2.board[1].base.hp == 2


def test_card_undyne_no_spear_summon():
    rig = TestRig.create(p1_deck=[1, 1, 1], p2_deck=[62])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

    rig.p1.end_turn()

    rig.p2.play_monster(rig.p2.hand[0])

    assert sum(1 for m in rig.p1.board if m) == 1
    assert rig.p1.board[2].hp == 2
    assert [m.template.name for m in rig.p2.board if m] == ["Undyne"]


@card(427)
class KillerCook(Monster):
    # Magic: Add Flour, Eggs and Milk to your hand.
    X: Var[TargetSelector] = Var(TargetSelector)

    magic = ForEach(
        [CARD_BY_NAME("Flour"), CARD_BY_NAME("Eggs"), CARD_BY_NAME("Milk")],
        var=X,
        effect=(X >> GENERATE_CARD()).to_hand()
    )


def test_card_killercook():
    rig = TestRig.create(p1_deck=[427])

    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.name for c in rig.p1.hand] == ["Dummy", "Dummy", "Dummy", "Flour", "Eggs", "Milk"]
