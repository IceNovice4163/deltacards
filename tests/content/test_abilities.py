from deltacards.dsl.api import *
from deltacards.model.enums import CardToggleableAbility

from ..card_templates import synthetic_card
from ..rig import TestRig


@synthetic_card(
    6,
    cost=1,
    attack=1,
    hp=4,
)
class Vegetoid(Monster):
    # Turn start: Heal 5 HP to you.
    turn_start = YOU.heal(5)


def test_card_vegetoid():
    rig = TestRig.create(p1_deck=[6])
    rig.p1.obj.hp = 10

    rig.p1.play_monster(rig.p1.hand[0], slot=0)

    rig.p1.end_turn()
    assert rig.p1.obj.hp == 10

    rig.p2.end_turn()
    assert rig.p1.obj.hp == 15


@synthetic_card(
    10,
    cost=1,
    attack=1,
    hp=4,
)
class Ice(Monster):
    # Dust: Paralyze the killer.
    dust = KILLER.paralyze()


def test_card_ice():
    rig = TestRig.create(p1_deck=[10, 10], p2_deck=[616, 616])

    ice_1 = rig.p1.hand[0]
    ice_2 = rig.p1.hand[1]
    rig.p1.play_monster(ice_1, slot=0)
    rig.p1.play_monster(ice_2, slot=1)
    rig.p1.end_turn()

    big_monster_1 = rig.p2.hand[0]
    big_monster_2 = rig.p2.hand[1]
    rig.p2.play_monster(big_monster_1, slot=0)
    rig.p2.play_monster(big_monster_2, slot=1)
    rig.p2.end_turn()

    # Attacker's Dust trigger test
    rig.p1.attack(ice_1, big_monster_1)
    assert ice_1.zone is CardZone.DUSTPILE
    assert big_monster_1.get_status(CardStatusId.PARALYZED) == 2
    rig.p1.end_turn()

    # Defender's Dust trigger test
    rig.p2.attack(big_monster_2, ice_2)
    assert ice_2.zone is CardZone.DUSTPILE
    assert big_monster_2.get_status(CardStatusId.PARALYZED) == 2


@synthetic_card(
    10005,
    cost=1,
    attack=1,
    hp=4,
    tribes=(Tribe.ARACHNID,),
)
class Spider(Monster):
    pass


@synthetic_card(
    10006,
    name="Spider Donut",
    cost=1,
    attack=1,
    hp=4,
    tribes=(Tribe.ARACHNID,),
)
class SpiderDonut(Monster):
    pass


@synthetic_card(
    10007,
    name="Spider Croissant",
    cost=1,
    attack=1,
    hp=4,
    tribes=(Tribe.ARACHNID,),
)
class SpiderCroissant(Monster):
    pass


@synthetic_card(
    478,
    cost=1,
    attack=1,
    hp=4,
    tribes=(Tribe.ARACHNID,),
)
class SpiderBakery(Monster):
    # Magic: Add a Spider to your hand and deck.
    # Synergy: Add a Spider Donut (to the hand) and a Spider Croissant (to the deck) instead.
    magic = Check(~SYNERGY_TRIGGERED).to(
        GENERATE_CARD("Spider").to_hand()
        >> GENERATE_CARD("Spider").to_deck()
    )

    synergy = (
        GENERATE_CARD("Spider Donut").to_hand()
        >> GENERATE_CARD("Spider Croissant").to_deck()
    )


def test_spider_bakery():
    rig = TestRig.create(p1_deck=[1, 478, 478, 478])

    rig.p1.play_monster(rig.p1.hand[0])
    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.name for c in rig.p1.hand][2:] == ["Spider"]

    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.name for c in rig.p1.hand][2:] == ["Spider Donut"]

    rig.p1.end_turn()
    rig.p2.end_turn()

    # Check that Synergy counts monster tribes played current turn only
    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.name for c in rig.p1.hand][3:] == ["Spider"]


def test_pippins():
    rig = TestRig.create(p1_deck=[1, 1, 288, 1, 288, 288, 288])
    assert [c.template.id for c in rig.p1.hand] == [1, 1, 288, 1]

    rig.p1.end_turn()
    rig.p2.end_turn()
    assert [c.template.id for c in rig.p1.hand] == [1, 1, 288, 1, 288, 288, 288]
    assert len(rig.p1.deck) == 18


@synthetic_card(
    760,
    cost=1,
    attack=1,
    hp=4,
    active_abilities={
        CardToggleableAbility.SHOCK,
        CardToggleableAbility.SUPPORT,
    },
)
class ButlerRalsei(Monster):
    # Shock: Give +2 HP to you.
    # Support: Program (1): Give the attacker +2 HP and trigger the Shock.
    shock = YOU.buff(hp=+2)

    support = Program(1).to(
        ATTACKER.buff(hp=+2)
        >> SELF.trigger_ability(SHOCK)
    )


def test_butlerralsei():
    rig = TestRig.create(p1_deck=[760, 1, 71])
    rig.p1.obj.hp = 10

    butler_ralsei = rig.p1.hand[0]
    dummy = rig.p1.hand[1]
    spell = rig.p1.hand[2]

    rig.p1.play_monster(butler_ralsei)
    rig.p1.play_monster(dummy)

    rig.p1.end_turn()
    rig.p2.end_turn()

    # Should trigger Support
    rig.p1.attack(dummy, rig.p2)
    assert dummy.hp == dummy.base.hp + 2
    assert rig.p1.hp == 10 + 2

    # Should NOT trigger Support
    rig.p1.attack(butler_ralsei, rig.p2)
    assert butler_ralsei.hp == butler_ralsei.base.hp
    assert rig.p1.hp == 10 + 2

    # Should trigger Shock
    rig.p1.play_spell(spell, target=dummy)
    assert rig.p1.hp == 10 + 2 + 2


@synthetic_card(
    289,
    cost=1,
    attack=1,
    hp=4,
)
class RedWagon(Monster):
    # Magic: Catch an ally monster. Dust: Release it to your hand with +3/+3.
    targets = ALLY_MONSTERS

    released_card: Var[Card] = Var(Card)

    magic = SELF.catch(TARGET)

    dust = SELF.release_caught_card(var=released_card).to(
        released_card.buff(attack=+3, hp=+3)
        >> released_card.to_hand(controller=released_card.controller)
    )


def test_card_redwagon():
    rig = TestRig.create(p1_deck=[1, 289, 129, 1])

    dummy = rig.p1.hand[0]
    catcher = rig.p1.hand[1]
    knife = rig.p1.hand[2]

    rig.p1.play_monster(dummy)
    rig.p1.play_monster(catcher, target=dummy)

    assert dummy.zone is CardZone.INVALID
    assert catcher.caught_card is not None
    assert catcher.caught_card.template_id == 1
    assert catcher.caught_card.controller_id == dummy.controller_id

    rig.p1.play_spell(knife, target=catcher)

    assert len(rig.p1.obj.board) == 0
    assert [c.template.id for c in rig.p1.hand] == [1, 1]
    assert rig.p1.hand[1].attack == rig.p1.hand[1].base.attack + 3
    assert rig.p1.hand[1].hp == rig.p1.hand[1].base.hp + 3


@synthetic_card(
    855,
    cost=1,
    active_abilities={
        CardToggleableAbility.BULLSEYE,
    },
)
class QuickDraw(Spell):
    # Make a monster Wanted and deal 3 DMG to it. Bullseye: Draw a card.
    targets = ALL_MONSTERS

    magic = (
        TARGET.add_keyword(WANTED)
        >> TARGET.hit(3)
    )

    bullseye = YOU.draw_next()


def test_quickdraw():
    rig = TestRig.create(p1_deck=[1, 1, 855, 855])

    dummy_bullseye = rig.p1.hand[0]
    dummy_no_bullseye = rig.p1.hand[1]

    rig.p1.play_monster(dummy_bullseye)
    rig.p1.play_monster(dummy_no_bullseye)

    dummy_bullseye.hp_missing = dummy_bullseye.hp - 3
    dummy_no_bullseye.hp_missing = dummy_no_bullseye.hp - 2
    assert [c.template.id for c in rig.p1.hand] == [855, 855]

    rig.p1.play_spell(rig.p1.hand[0], target=dummy_bullseye)
    assert dummy_bullseye.zone is CardZone.DUSTPILE
    assert [c.template.id for c in rig.p1.hand] == [855, 1]

    rig.p1.play_spell(rig.p1.hand[0], target=dummy_no_bullseye)
    assert dummy_bullseye.zone is CardZone.DUSTPILE
    assert [c.template.id for c in rig.p1.hand] == [1]


@synthetic_card(
    452,
    cost=0,
)
class Recruitment(Spell):
    pass


@synthetic_card(
    903,
    cost=1,
    attack=1,
    hp=4,
    active_abilities={
        CardToggleableAbility.BULLSEYE,
    },
)
class ZootSusie(Monster):
    # Magic: Deal 4 DMG to a monster.
    # Bullseye: Deal 3 DMG to its adjacent monsters and add a Recruitment to your hand.
    targets = ALL_MONSTERS

    magic = TARGET.hit(4)

    bullseye = (
        ADJACENT(TARGET).hit(3)
        >> GENERATE_CARD("Recruitment").to_hand()
    )


def test_zootsusie():
    rig = TestRig.create(p1_deck=[1, 1, 1, 1], p2_deck=[903])

    for _ in range(4):
        rig.p1.play_monster(rig.p1.hand[0])

    rig.p1.end_turn()

    rig.p2.play_monster(rig.p2.hand[0], target=rig.p1.board[2])
    assert rig.p2.hand[-1].template.name == "Recruitment"
    assert [(c.template.id if c else None) for c in rig.p1.board] == [1, 1, None, 1]
    assert [(c.hp if c else None) for c in rig.p1.board] == [4, 1, None, 1]


def test_zootsusie_attack():
    rig = TestRig.create(p1_deck=[903], p2_deck=[1, 1, 1, 1])

    defender = rig.p1.hand[0]

    rig.p1.play_monster(defender)
    rig.p1.end_turn()

    for _ in range(4):
        rig.p2.play_monster(rig.p2.hand[0])

    attacker = rig.p2.board[2]
    attacker.buff(attack=defender.hp - attacker.attack, hp=defender.attack - attacker.hp)
    attacker.add_keyword(CardKeyword.HASTE)

    rig.p2.attack(attacker, defender)

    assert sum(1 for m in rig.p1.board if m) == 0
    assert rig.p1.hand[-1].template.name == "Recruitment"
    assert [(c.template.id if c else None) for c in rig.p2.board] == [1, 1, None, 1]
    assert [(c.hp if c else None) for c in rig.p2.board] == [4, 1, None, 1]
