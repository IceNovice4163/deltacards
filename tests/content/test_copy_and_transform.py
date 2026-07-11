from deltacards.dsl.api import *
from deltacards.model.cards import CardBuffs

from ..rig import TestRig


@card(379)
class Crown(Spell):
    # Give a monster +1/+2. If it's a C-Round, turn it into a K-Round instead. Draw a card.
    targets = ALL_MONSTERS

    magic = (
        Check(TARGET & (TEMPLATE_NAME == "C-Round")).to(
            TARGET.turn_into(GENERATE_CARD("K-Round")),
            else_=TARGET.buff(attack=+1, hp=+2)
        )
        >> YOU.draw_next()
    )


def test_card_crown():
    rig = TestRig.create(p1_deck=[379, 379, 1, 378])

    spell_1 = rig.p1.hand[0]
    spell_2 = rig.p1.hand[1]
    dummy = rig.p1.hand[2]
    c_round = rig.p1.hand[3]

    rig.p1.play_monster(dummy, slot=0)
    rig.p1.play_monster(c_round, slot=3)

    rig.p1.play_spell(spell_1, target=dummy)
    assert rig.p1.board[0].template.name == "Dummy"
    assert rig.p1.board[0].buffs.attack == 1
    assert rig.p1.board[0].buffs.max_hp == 2

    rig.p1.play_spell(spell_2, target=c_round)
    assert rig.p1.board[3].template.name == "K-Round"
    assert rig.p1.board[3].buffs.attack == 0
    assert rig.p1.board[3].buffs.max_hp == 0


@card(394)
class MisterElegance(Monster):
    # Magic: Switch: [Gain +1/+1 and Armor] or [Summon a copy of this].
    magic = Switch(
        left=SELF.buff(attack=+1, hp=+1) >> SELF.add_keyword(ARMOR),
        right=(SELF >> COPY()).summon()
    )


def test_card_misterelegance():
    rig = TestRig.create(p1_deck=[394, 394])

    rig.p1.play_monster(rig.p1.hand[0], slot=0)
    assert sum(1 for m in rig.p1.board if m) == 1
    assert rig.p1.board[0]
    assert rig.p1.board[0].template.name == "Mister Elegance"
    assert rig.p1.board[0].buffs.attack == 1
    assert rig.p1.board[0].buffs.max_hp == 1
    assert rig.p1.board[0].has_keyword(CardKeyword.ARMOR)

    rig.p1.play_monster(rig.p1.hand[0], slot=3)
    assert sum(1 for m in rig.p1.board if m) == 3
    assert rig.p1.board[0]
    assert rig.p1.board[1]
    assert not rig.p1.board[2]
    assert rig.p1.board[3]

    for index in (3, 1):
        assert rig.p1.board[index].template.name == "Mister Elegance"
        assert not rig.p1.board[index].has_keyword(CardKeyword.ARMOR)

    assert rig.p1.board[1].creator_id == rig.p1.board[3].id
    assert rig.p1.board[1].creator_base_identity == ('card', 394)


@card(442)
class SandDog(Monster):
    # Magic: Summon an exact copy of this.
    magic = (SELF >> EXACT_COPY()).summon()


def test_card_sanddog():
    rig = TestRig.create(p1_deck=[442])

    rig.p1.hand[0].buff(cost=+1, attack=+2, hp=+3)
    rig.p1.hand[0].add_keyword(CardKeyword.CHARGE)
    rig.p1.hand[0].set_status(CardStatusId.PARALYZED, 2)

    rig.p1.play_monster(rig.p1.hand[0])

    for index in (0, 1):
        assert rig.p1.board[index].template.name == "Sand Dog"
        assert rig.p1.board[index].buffs == CardBuffs(cost=+1, attack=+2, max_hp=+3)
        assert rig.p1.board[index].has_keyword(CardKeyword.CHARGE)
        assert rig.p1.board[index].get_status(CardStatusId.PARALYZED) == 2

    assert rig.p1.board[1].creator_id == rig.p1.board[0].id
    assert rig.p1.board[1].creator_base_identity == ('card', 442)


@card(631)
class Shovel(Monster):
    magic = Check(LOOP_COPY & HAND & ~HAS_STATUS(LOOP)).to(
        Program(3).to(
            LOOP_COPY.erase().to(
                SELF.buff(attack=+3, hp=+4)
            )
        )
    )


def test_shovel():
    rig = TestRig.create(p1_deck=[631, 631])

    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.id for c in rig.p1.hand] == [631, 1, 1]
    assert rig.p1.board[0].attack == rig.p1.board[0].base.attack + 3
    assert rig.p1.board[0].hp == rig.p1.board[0].base.hp + 4

    rig.p1.obj.gold = rig.p1.hand[0].cost
    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.id for c in rig.p1.hand] == [1, 1, 631]
    assert rig.p1.board[1].attack == rig.p1.board[1].base.attack
    assert rig.p1.board[1].hp == rig.p1.board[1].base.hp
