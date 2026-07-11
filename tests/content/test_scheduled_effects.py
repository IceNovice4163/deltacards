from deltacards.dsl.api import *

from ..rig import TestRig


@card(36)
class SnowdrakesMom(Monster):
    # Delay: Summon a Vegetoid. Give it +1/+1 and TRANSPARENCY if this has any ATK buffs.
    res: Var[StepResult] = Var(StepResult)

    magic = SELF.schedule_delay_effect()

    delay = GENERATE_CARD("Vegetoid").summon().store_result(res).to(
        Check(SELF.buffs.attack > 0).to(
            Buff(target=res.monster_id, attack=+1, hp=+1)
            >> AddKeyword(target=res.monster_id, keyword=TRANSPARENCY)
        )
    )


def test_card_snowdrakesmom():
    rig = TestRig.create(p1_deck=[36, 36])

    monster_1 = rig.p1.hand[0]
    monster_2 = rig.p1.hand[1]

    rig.p1.play_monster(monster_1)
    rig.p1.play_monster(monster_2)
    monster_1.buff(attack=+1)
    monster_2.buff(hp=+1)
    assert len(rig.p1.obj.board) == 2

    rig.p1.end_turn()
    assert len(rig.p1.obj.board) == 4

    assert rig.p1.board[2].has_keyword(CardKeyword.TRANSPARENCY)
    assert rig.p1.board[2].buffs.attack == 1
    assert rig.p1.board[2].buffs.max_hp == 1

    assert not rig.p1.board[3].has_keyword(CardKeyword.TRANSPARENCY)
    assert rig.p1.board[3].buffs.attack == 0
    assert rig.p1.board[3].buffs.max_hp == 0


def test_card_frozenenergy():
    rig = TestRig.create(p1_deck=[1, 1, 71, 71])

    dummy_1 = rig.p1.hand[0]
    dummy_2 = rig.p1.hand[1]

    rig.p1.play_monster(dummy_1)
    rig.p1.play_monster(dummy_2)
    rig.p1.play_spell(rig.p1.hand[0], target=dummy_1)
    rig.p1.play_spell(rig.p1.hand[0], target=dummy_2)
    dummy_2.buff(cost=+1)
    assert dummy_1.get_status(CardStatusId.PARALYZED) == 0
    assert dummy_2.get_status(CardStatusId.PARALYZED) == 0

    rig.p1.end_turn()
    assert dummy_1.get_status(CardStatusId.PARALYZED) == 2
    assert dummy_2.get_status(CardStatusId.PARALYZED) == 0


@card(128)
class FroggitTrio(Spell):
    frog_1: Var[Card] = Var(Card)
    frog_2: Var[Card] = Var(Card)
    reward_frog: Var[Card] = Var(Card)

    magic = (
        SetVar(var=frog_1, value=GENERATE_CARD("Froggit"))
        >> frog_1.add_keyword(HASTE)
        >> frog_1.summon()

        >> SetVar(var=frog_2, value=GENERATE_CARD("Froggit"))
        >> frog_2.add_keyword(HASTE)
        >> frog_2.summon()

        >> SELF.schedule_delay_effect()
    )

    delay = Check(
        frog_1.dead & frog_2.dead
    ).to(
        SetVar(var=reward_frog, value=GENERATE_CARD("Froggit"))
        >> reward_frog.set_stats(cost=0)
        >> reward_frog.add_keyword(HASTE)
        >> reward_frog.to_hand()
    )


def test_card_froggittrio():
    rig = TestRig.create(p1_deck=[128, 128])

    rig.p1.play_spell(rig.p1.hand[0])

    assert [m.template.name for m in rig.p1.board if m] == ["Froggit", "Froggit"]

    rig.p1.end_turn()
    assert [c.template.name for c in rig.p1.hand][3:] == []
