from deltacards.dsl.api import *

from ..rig import TestRig


@card(236)
class HotDogVulkin(Monster):
    # Magic: Deal 3 DMG to an opponent.
    magic = OPPONENT.hit(3)


def test_card_hotdogvulkin():
    rig = TestRig.create(p1_deck=[236])

    rig.p1.play_monster(rig.p1.hand[0], slot=0)
    assert rig.p2.obj.hp == rig.p2.obj.max_hp - 3


@card(23)
class Migospel(Monster):
    # Magic: Give a monster +3 HP.
    targets = ALL_MONSTERS

    magic = TARGET.buff(hp=+3)


def test_card_migospel():
    rig = TestRig.create(p1_deck=[1, 23])

    dummy = rig.p1.hand[0]
    migospel = rig.p1.hand[1]

    rig.p1.play_monster(dummy, slot=0)
    rig.p1.play_monster(migospel, slot=1, target=dummy)

    assert dummy.hp == dummy.base.hp + 3


def test_card_knife():
    rig = TestRig.create(p1_deck=[1], p2_deck=[129])

    dummy = rig.p1.hand[0]
    rig.p1.play_monster(dummy, slot=0)

    dummy.buff(cost=+1)
    dummy_cost = dummy.cost

    rig.p1.end_turn()

    rig.p2.play_spell(rig.p2.hand[0], target=dummy)

    assert dummy.zone is CardZone.DUSTPILE
    assert len(rig.p1.obj.board) == 0
    assert rig.p2.hp == rig.p2.max_hp - dummy_cost


@card(79)
class Penetration(Spell):
    # Silence a monster.
    targets = ALL_MONSTERS

    magic = TARGET.silence()


def test_card_penetration():
    rig = TestRig.create(p1_deck=[1, 79])

    dummy = rig.p1.hand[0]
    spell = rig.p1.hand[1]

    rig.p1.play_monster(dummy)
    dummy.buff(attack=+2, hp=+3)
    dummy.add_keyword(CardKeyword.TAUNT)
    dummy.set_status(CardStatusId.PARALYZED, 2)

    assert dummy.attack == dummy.base.attack + 2
    assert dummy.hp == dummy.base.hp + 3
    assert dummy.has_keyword(CardKeyword.TAUNT)
    assert dummy.get_status(CardStatusId.PARALYZED) == 2

    rig.p1.play_spell(spell, target=dummy)

    assert dummy.has_keyword(CardKeyword.SILENCED)
    assert not dummy.has_keyword(CardKeyword.TAUNT)
    assert dummy.get_status(CardStatusId.PARALYZED) == 0
    assert dummy.attack == dummy.base.attack
    assert dummy.max_hp == dummy.base.hp
    assert dummy.hp == dummy.base.hp
