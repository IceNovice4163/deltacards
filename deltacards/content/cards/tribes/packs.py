from deltacards.dsl.api import *


@card(875)
class Pack(Spell):
    magic = YOU.choose(
        DISCOVER(IS_MONSTER, NON_TOKEN, n=4)
    ).to(
        CHOICE_SELECTED.to_hand()
    )


@card(876)
class SuperPack(Spell):
    pack_cards: Var[TargetSelector] = Var(TargetSelector)

    magic = (
        SetVar(
            var=pack_cards,
            value=(
                DISCOVER(IS_MONSTER, RARITY == CardRarity.COMMON)
                | DISCOVER(IS_MONSTER, RARITY == CardRarity.RARE)
                | DISCOVER(IS_MONSTER, RARITY == CardRarity.EPIC)
                | DISCOVER(IS_MONSTER, RARITY == CardRarity.LEGENDARY)
            )
        )
        >> YOU.choose(pack_cards).to(
            CHOICE_SELECTED.buff(cost=-2)
            >> CHOICE_SELECTED.to_hand()
        )
    )


@card(877)
class FinalPack(Spell):
    pack_cards: Var[TargetSelector] = Var(TargetSelector)

    magic = (
        SetVar(
            var=pack_cards,
            value=(
                DISCOVER(IS_MONSTER, RARITY == CardRarity.RARE)
                | DISCOVER(IS_MONSTER, RARITY == CardRarity.EPIC)
                | DISCOVER(IS_MONSTER, RARITY == CardRarity.LEGENDARY)
                | DISCOVER(IS_MONSTER, RARITY == CardRarity.DETERMINATION)
            )
        )
        >> YOU.choose(pack_cards).to(
            CHOICE_SELECTED.buff(cost=-2)
            >> CHOICE_SELECTED.add_keyword(HASTE)
            >> CHOICE_SELECTED.to_hand()
        )
    )
