from .selectors import NextLostSoulSelector, SELF, YOU
from .transforms import GENERATE
from .values import HAS_ARTIFACT


def Program(amount: int):
    from actions import SpendGold
    return SpendGold(player=YOU, amount=amount)


def Switch(left, right):
    from effects import Check
    return Check(SELF.pos <= 1).to(left, else_=right)


def SwitchPiece(left, right):
    from effects import Check
    return Check(YOU & HAS_ARTIFACT("Reverberation")).to(
        left >> right,
        else_=Switch(left, right)
    )


NEXT_LOST_SOUL = NextLostSoulSelector() >> GENERATE()
