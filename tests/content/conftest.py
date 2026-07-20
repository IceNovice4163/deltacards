from deltacards.dsl.api import *

from ..card_templates import synthetic_card


@synthetic_card(
    71,
    cost=2,
)
class FrozenEnergy(Spell):
    # Give a monster +2/+2 and HASTE. Delay: If its COST is the same as its base COST, Paralyze it.
    targets = ALL_MONSTERS

    magic = (
        TARGET.buff(attack=+2, hp=+2)
        >> TARGET.add_keyword(HASTE)
        >> SELF.schedule_delay_effect()
    )

    delay = Check(TARGET.cost == TARGET.base.cost).to(TARGET.paralyze())


@synthetic_card(
    79,
    cost=1,
)
class Penetration(Spell):
    targets = ALL_MONSTERS

    magic = TARGET.silence()


@synthetic_card(
    83,
    cost=1,
)
class Shopping(Spell):
    # Draw 3 cards costing 5 GOLD or less.
    magic = YOU.draw(
        (DECK & (COST <= 5)).first()
    ) * 3


@synthetic_card(
    129,
    cost=4,
)
class Knife(Spell):
    # Kill a monster. Deal its COST as DMG to you.
    targets = ALLY_MONSTERS | ENEMY_MONSTERS

    kill_result: Var[StepResult] = Var(StepResult)

    magic = (
        TARGET.kill().store_result(kill_result).to(
            YOU.hit(kill_result.monster.cost)
        )
    )


@synthetic_card(
    288,
    cost=1,
    attack=1,
    hp=4,
)
class Pippins(Monster):
    # Turbo: If you have 6 or less cards in your hand, draw a card.
    turbo = Check(COUNT(HAND) <= 6).to(
        YOU.draw_next()
    )


@synthetic_card(
    552,
    name="Change of Winds",
    cost=0,
)
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


@synthetic_card(
    578,
    name="Crystal Shard",
    cost=2,
)
class CrystalShard(Spell):
    targets = ALLIES | ENEMIES

    magic = TARGET.hit(3)


@synthetic_card(
    616,
    cost=9,
    attack=10,
    hp=10,
)
class Banana(Monster):
    pass
