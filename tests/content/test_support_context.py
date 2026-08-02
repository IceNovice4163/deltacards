from deltacards.dsl.api import *
from deltacards.model.enums import CardToggleableAbility

from ..card_templates import synthetic_card
from ..rig import TestRig


@synthetic_card(
    375,
    name="Green Clover",
    cost=0,
    attack=2,
    hp=2,
)
class GreenClover(Monster):
    pass


@synthetic_card(
    10011,
    cost=1,
    attack=1,
    hp=4,
)
class LeaflingAttacker(Monster):
    pass


@synthetic_card(
    10012,
    cost=1,
    attack=0,
    hp=20,
)
class LeaflingDefender(Monster):
    pass


@synthetic_card(
    976,
    cost=1,
    attack=1,
    hp=4,
    active_abilities={
        CardToggleableAbility.SUPPORT,
    },
)
class Leafling(Monster):
    generated_cards: Var[TargetSelector] = Var(TargetSelector)
    generated_card: Var[TargetSelector] = Var(TargetSelector)

    support = Check(
        ATTACKER & (TEMPLATE_NAME != "Green Clover")
    ).to(
        SetVar(
            var=generated_cards,
            value=GENERATE_CARD(
                "Green Clover",
                count=EMPTY_SLOTS(BOARD)
            )
        )
        >> generated_cards.summon()
        >> ForEach(
            generated_cards,
            var=generated_card,
            effect=generated_card.force_attack(DEFENDER)
        )
    )


def test_leafling_support_generates_for_empty_slots_and_attacks_defender():
    rig = TestRig.create(
        p1_deck=[976, 10011],
        p2_deck=[10012],
    )

    leafling = rig.p1.hand[0]
    attacker = rig.p1.hand[1]

    rig.p1.play_monster(leafling, slot=0)
    rig.p1.play_monster(attacker, slot=1)
    rig.p1.end_turn()

    defender = rig.p2.hand[0]
    rig.p2.play_monster(defender, slot=0)
    rig.p2.end_turn()

    hp_before = defender.hp
    rig.p1.attack(attacker, defender)

    clovers = [
        monster
        for monster in rig.p1.board
        if (
            monster is not None
            and monster.template.name == "Green Clover"
        )
    ]

    assert len(clovers) == 2
    assert [clover.pos for clover in clovers] == [2, 3]
    assert all(clover.has_attacked for clover in clovers)

    assert defender.hp == (
        hp_before
        - attacker.attack
        - sum(clover.attack for clover in clovers)
    )

    resolved_attacks = [
        res
        for res in rig.game.log
        if (
            isinstance(res, AttackResolvedResult)
            and res.defender_id == defender.id
        )
    ]

    assert len(resolved_attacks) == 3
    assert {
        res.attacker_id
        for res in resolved_attacks
    } == {
        attacker.id,
        *(clover.id for clover in clovers),
    }
