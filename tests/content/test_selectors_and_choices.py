from deltacards.dsl.api import *

from ..rig import TestRig


@card(83)
class Shopping(Spell):
    # Draw 3 cards costing 5 GOLD or less.
    magic = YOU.draw(
        (DECK & (COST <= 5)).first()
    ) * 3


def test_card_shopping():
    rig = TestRig.create(p1_deck=[83, 1, 1, 1, 616, 616])

    assert [c.template.id for c in rig.p1.hand] == [83, 1, 1, 1]
    rig.p1.play_spell(rig.p1.hand[0])
    assert [c.template.id for c in rig.p1.hand] == [1] * 6


@card(400)
class Cogwheel(Monster):
    # Turn end: Send the most expensive card in your hand to your deck and draw a card.
    turn_end = (HAND >> MAX(COST)).to_deck() >> YOU.draw_next()


def test_card_cogwheel():
    rig = TestRig.create(p1_deck=[400, 1, 616, 1])

    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.id for c in rig.p1.hand] == [1, 616, 1]
    rig.p1.end_turn()
    assert len(rig.p1.hand) == 3
    assert [c.template.id for c in rig.p1.hand][:2] == [1, 1]


@card(552)
class ChangeOfWinds(Spell):
    # Look at the next 2 cards in your deck.
    # Choose one to draw.
    # Send the other to the bottom of your deck.
    # Give them -1 COST.
    magic = YOU.choose(DECK[:2]).to(
        YOU.draw(CHOICE_SELECTED)
        >> CHOICE_NOT_SELECTED.to_deck(pos='bottom')
        >> (CHOICE_SELECTED | CHOICE_NOT_SELECTED).buff(cost=-1)
    )


def test_card_changeofwinds():
    rig = TestRig.create(p1_deck=[552, 1, 1, 1, 616, 1])

    rig.p1.play_spell(rig.p1.hand[0])
    choices = rig.get_choices()
    assert [c.template.id for c in choices] == [616, 1]

    rig.p1.choose([choices[0]])
    assert choices[0].zone is CardZone.HAND
    assert choices[0].cost == choices[0].base.cost - 1
    assert choices[1].zone is CardZone.DECK
    assert choices[1].cost == choices[1].base.cost - 1


@card(246)
class Editor2(Monster):
    # Magic: Look at 5 random monsters and choose one. Add it to your hand.
    magic = YOU.choose(
        DISCOVER(IS_MONSTER, n=5)
    ).to(
        CHOICE_SELECTED.to_hand()
    )


def test_card_editor2():
    rig = TestRig.create(p1_deck=[246, 246, 246])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

        choices = rig.get_choices()
        template_ids = [card.template.id for card in choices]
        assert len(set(template_ids)) == len(template_ids)

        rig.p1.choose([choices[0]])
        assert len(rig.p1.hand) == 4
        assert rig.p1.hand[-1].id == choices[0].id


@card(76)
class Strength(Spell):
    # Give 3 random ally monsters +1/+1
    magic = (ALLY_MONSTERS >> RANDOM(3)).buff(attack=+1, hp=+1)


def test_card_strength():
    rig = TestRig.create(p1_deck=[76, 1, 1, 1])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[1])

    rig.p1.play_spell(rig.p1.hand[0])

    for m in rig.p1.board:
        if not m:
            continue

        assert m.attack == m.base.attack + 1
        assert m.hp == m.base.hp + 1


@card(468)
class Rudolph(Monster):
    # Need: You have no other cards named Rudolph in your hand. Magic: Give +5 HP to you.
    need = ~EXISTS(
        HAND
        & ~SELF
        & (TEMPLATE_NAME == "Rudolph")
    )

    magic = YOU.buff(hp=+5)


def test_rudolph():
    rig = TestRig.create(p1_deck=[468, 468])
    rig.p1.obj.hp = 10

    assert not rig.game.card_need_fulfilled(rig.p1.hand[0])
    rig.p1.play_monster(rig.p1.hand[0])
    assert rig.p1.hp == 10

    assert rig.game.card_need_fulfilled(rig.p1.hand[0])
    rig.p1.play_monster(rig.p1.hand[0])
    assert rig.p1.hp == 10 + 5
