from typing import Any

from deltacards.actions.base import Action
from deltacards.actions.standard import Move, SetEntityState, SpendGold
from deltacards.dsl.aggregates import COUNT
from deltacards.dsl.selectors import BOARD, BOARD_OF, DECK, HAND, HAND_OF, NextLostSoulSelector, SELF, YOU
from deltacards.dsl.transforms import GENERATE_CARD
from deltacards.dsl.values import EMPTY_SLOTS, HAS_ARTIFACT
from deltacards.dsl.vars import StateVar
from deltacards.engine.constants import MAX_HAND_SIZE
from deltacards.engine.effects import Check, EffectBase, For
from deltacards.model.enums import CardZone


def Program(amount: int):
    return SpendGold(player=YOU, amount=amount, reason='program')


def Switch(left, right):
    return Check(SELF & BOARD).to(
        Check(SELF.pos <= 1).to(left, else_=right)
    )


def SwitchPiece(left, right):
    return Check(YOU & HAS_ARTIFACT("Endgame")).to(
        left >> right,
        else_=Switch(left, right)
    )


def DrawUpTo(count: int):
    return For(
        count,
        effect=Check((COUNT(HAND) < MAX_HAND_SIZE) & (COUNT(DECK) > 0)).to(
            YOU.draw_next()
        )
    )


def FillBoard(player, card):
    return For(
        EMPTY_SLOTS(BOARD_OF(player)),
        (card >> GENERATE_CARD(controller=player)).summon(controller=player)
    )


def FillHand(player, card):
    return For(
        EMPTY_SLOTS(HAND_OF(player)),
        Move(target=card >> GENERATE_CARD(controller=player), zone=CardZone.HAND)
    )


def OncePerTurn(
    state_var: StateVar[Any],
    effect: EffectBase | Action,
):
    return Check(state_var != YOU.turn).to(
        effect.to(
            SetEntityState(
                state_var=state_var,
                value=YOU.turn,
            )
        )
    )


NEXT_LOST_SOUL = NextLostSoulSelector() >> GENERATE_CARD()
