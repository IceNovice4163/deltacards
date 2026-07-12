from deltacards.dsl.api import *


@card(28)
class Chara(Monster):
    targets = ALL_MONSTERS

    magic = (
        TARGET.erase()
        >> YOU.add_artifact(ARTIFACT_BY_NAME("Genocide"))
    )


@card(65)
class Frisk(Monster):
    magic = (
        Check(PLAYER_SOUL(player=OPPONENT) == "patience").to(
            YOU.add_artifact(ARTIFACT_BY_NAME("Toy Knife")),
            else_=Check(PLAYER_SOUL(player=OPPONENT) == "bravery").to(
                YOU.add_artifact(ARTIFACT_BY_NAME("Tough Glove")),
                else_=Check(PLAYER_SOUL(player=OPPONENT) == "integrity").to(
                    YOU.add_artifact(ARTIFACT_BY_NAME("Ballet Shoes")),
                    else_=Check(PLAYER_SOUL(player=OPPONENT) == "kindness").to(
                        YOU.add_artifact(ARTIFACT_BY_NAME("Burnt Pan")),
                        else_=Check(PLAYER_SOUL(player=OPPONENT) == "justice").to(
                            YOU.add_artifact(ARTIFACT_BY_NAME("Empty Gun")),
                            else_=Check(PLAYER_SOUL(player=OPPONENT) == "determination").to(
                                YOU.add_artifact(ARTIFACT_BY_NAME("Worn Dagger")),
                                else_=Check(PLAYER_SOUL(player=OPPONENT) == "perseverance").to(
                                    YOU.add_artifact(ARTIFACT_BY_NAME("Torn Notebook"))
                                )
                            )
                        )
                    )
                )
            )
        )
        >> GENERATE_CARD("ACT Button").to_hand()
    )


@card(203)
class AngelOfDeath(Monster):
    targets = ALL_MONSTERS

    copied_card: Var[Card] = Var(Card)

    magic = (
        SetVar(var=copied_card, value=TARGET >> EXACT_COPY())
        >> copied_card.add_keyword(HASTE)
        >> copied_card.summon()
    )

    dust = For(
        EMPTY_SLOTS(BOARD),
        NEXT_LOST_SOUL.summon()
    )


@card(801)
class TheBarrier(Monster):
    magic = OPPONENT.hit(
        COUNT((DUSTPILE | OPPONENT_DUSTPILE) & IS_MONSTER) // 2
    )
