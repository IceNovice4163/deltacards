from deltacards.dsl.selectors import NextLostSoulSelector, SELF, YOU
from deltacards.dsl.transforms import GENERATE
from deltacards.dsl.values import HAS_ARTIFACT


def Program(amount: int):
    from deltacards.actions.standard import SpendGold
    return SpendGold(player=YOU, amount=amount)


def Switch(left, right):
    from deltacards.engine.effects import Check
    return Check(SELF.pos <= 1).to(left, else_=right)


def SwitchPiece(left, right):
    from deltacards.engine.effects import Check
    return Check(YOU & HAS_ARTIFACT("Reverberation")).to(
        left >> right,
        else_=Switch(left, right)
    )


NEXT_LOST_SOUL = NextLostSoulSelector() >> GENERATE()
