from deltacards.dsl.api import *

from ..card_templates import synthetic_card
from ..rig import TestRig


@synthetic_card(
    10010,
    cost=1,
    attack=4,
    hp=6,
)
class NegativeEffectTarget(Monster):
    pass


@synthetic_card(
    980,
    cost=1,
    attack=1,
    hp=4,
)
class Seth(Monster):
    # Need: 3+ monsters with negative effects.
    # Magic: Give all enemy monsters -2/-2.
    need = COUNT(
        ALL_MONSTERS & HAS_NEGATIVE_EFFECTS
    ) >= 3

    magic = ENEMY_MONSTERS.buff(attack=-2, hp=-2)


def test_seth_has_negative_effects_need():
    rig = TestRig.create(
        p1_deck=[980],
        p2_deck=[10010, 10010, 10010, 10010],
    )

    seth = rig.p1.hand[0]

    rig.p1.end_turn()

    targets = rig.p2.hand[:4]
    for target in targets:
        rig.p2.play_monster(target)

    damaged = targets[0]
    cost_increased = targets[1]
    disarmed = targets[2]
    paralyzed = targets[3]

    damaged.hp_missing = 1

    assert not damaged.has_negative_effects()
    assert not rig.game.card_need_fulfilled(seth)

    cost_increased.buff(cost=+1)
    disarmed.add_keyword(DISARMED)

    assert cost_increased.has_negative_effects()
    assert disarmed.has_negative_effects()
    assert not rig.game.card_need_fulfilled(seth)

    paralyzed.set_status(PARALYZED, 2)

    assert paralyzed.has_negative_effects()
    assert rig.game.card_need_fulfilled(seth)

    rig.p2.end_turn()
    rig.p1.play_monster(seth)

    assert damaged.has_negative_effects()

    played_result = next(
        res
        for res in reversed(rig.game.log)
        if (
            isinstance(res, CardPlayedResult)
            and res.card_id == seth.id
        )
    )

    assert played_result.has_need_condition
    assert played_result.need_fulfilled

    for target in targets:
        assert target.buffs.attack == -2
        assert target.buffs.max_hp == -2
        assert target.attack == target.base.attack - 2
        assert target.max_hp == target.base.hp - 2
