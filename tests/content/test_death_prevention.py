from deltacards.dsl.api import *

from ..card_templates import synthetic_card
from ..rig import TestRig


@synthetic_card(
    106,
    cost=9,
    attack=7,
    hp=8,
)
class TheHeroine(Monster):
    # Magic: Instead of dying, Erase 2 cards in your hand to return with -1/-2 base stats.
    def on_would_die(self, entity: Entity, game, **kwargs):
        hand = game.player(self.controller_id).hand
        if entity.id == self.id and self.base.hp > 2 and len(hand) >= 2:
            return [
                [hand.cards[i].actions.erase() for i in range(2)]
                + [self.revive]
            ]

        return None

    def revive(self, ctx, **kwargs):
        base_attack = self.base.attack
        base_hp = self.base.hp

        self._reset()

        self.set_base_stats(attack=base_attack - 1, hp=base_hp - 2)


def test_theheroine_death_prevention_on_kill():
    rig = TestRig.create(p1_deck=[106, 129, 1, 1])

    monster = rig.p1.hand[0]
    knife = rig.p1.hand[1]

    base_attack = monster.base.attack
    base_hp = monster.base.hp

    rig.p1.play_monster(monster, slot=3)
    rig.p1.play_spell(knife, target=monster)

    assert monster.zone is CardZone.BOARD
    assert monster.pos == 3
    assert monster.base.attack == base_attack - 1
    assert monster.base.hp == base_hp - 2
    assert len(rig.p1.hand) == 0


def test_theheroine_death_prevention_on_combat_damage():
    rig = TestRig.create(p1_deck=[106, 1, 1, 1], p2_deck=[616])

    monster = rig.p1.hand[0]

    base_attack = monster.base.attack
    base_hp = monster.base.hp

    rig.p1.play_monster(monster, slot=3)
    rig.p1.end_turn()

    big_monster = rig.p2.hand[0]
    rig.p2.play_monster(big_monster)
    rig.p2.end_turn()

    rig.p1.attack(monster, big_monster)

    assert monster.zone is CardZone.BOARD
    assert monster.pos == 3
    assert monster.base.attack == base_attack - 1
    assert monster.base.hp == base_hp - 2
    assert len(rig.p1.hand) == 2


def test_theheroine_death_prevention_failure():
    rig = TestRig.create(p1_deck=[106, 129, 1, 1])

    monster = rig.p1.hand[0]
    knife = rig.p1.hand[1]
    dummy = rig.p1.hand[2]

    rig.p1.play_monster(monster, slot=3)
    rig.p1.play_monster(dummy)
    rig.p1.play_spell(knife, target=monster)

    assert monster.zone is CardZone.DUSTPILE
    assert len(rig.p1.hand) == 1
