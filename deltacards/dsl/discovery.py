from deltacards.dsl.core import Predicate, TargetSelector
from deltacards.dsl.selectors import CARD_LIBRARY, SELF, YOU
from deltacards.dsl.transforms import GENERATE, RANDOM


def DISCOVER(
    *constraints: Predicate,
    n: int = 1,
    pool: TargetSelector | None = None,
    controller: TargetSelector = YOU,
    creator: TargetSelector = SELF,
) -> TargetSelector:
    if pool is None:
        pool = CARD_LIBRARY

    selector: TargetSelector = pool
    for predicate in constraints:
        selector = selector & predicate

    return selector >> RANDOM(n) >> GENERATE(controller=controller, creator=creator)
