from typing import Literal, TypeAlias


BaseIdentity: TypeAlias = tuple[str, int | str]

GoldSpendReason: TypeAlias = Literal[
    'play_monster',
    'play_spell',
    'program',
    'effect',
]

EnchantmentRemovalReason: TypeAlias = Literal[
    'expired',
    'removed',
    'replaced',
    'transformed',
]
