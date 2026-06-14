from enums import Ability, CardKeyword

from .core import (
    AmbiguousTargetError,
    NoTargetsError,
    Predicate,
    TargetSelector,
    TargetingError,
    Transform,
    ValueExpr,
)

from .selectors import (
    SELF,
    TARGET,
    KILLER,
    ATTACKER,
    YOU,
    CONTROLLER,
    OPPONENT,
    TURN_PLAYER,

    BOARD,
    HAND,
    DECK,
    DUSTPILE,
    ERASED,

    OPPONENT_BOARD,
    OPPONENT_HAND,
    OPPONENT_DECK,
    OPPONENT_DUSTPILE,
    OPPONENT_ERASED,

    ALLY_MONSTERS,
    ENEMY_MONSTERS,
    ALLIES,
    ENEMIES,

    LEFT,
    RIGHT,
    ADJACENT,
    FRONT,
    LEFT_OF,
    RIGHT_OF,

    LEFT_IN_HAND,
    RIGHT_IN_HAND,
    ADJACENT_IN_HAND,

    BOARD_OF,
    HAND_OF,
    DECK_OF,
    DUSTPILE_OF,
    ERASED_OF,

    CONTROLLER_OF,
    OPPONENT_OF,

    CARD_LIBRARY,
    CARD_BY_NAME,
)

from .values import (
    ID,
    TEMPLATE_ID,
    COST,
    RARITY,
    ATTACK,
    HP,
    MAX_HP,
    CREATOR_ID,
    BASE_COST,
    BASE_ATTACK,
    BASE_HP,
    COUNT,
    EMPTY_SLOTS,
    CLAMP,
    LEAST,
    GREATEST,
    SYNERGY_TRIGGERED,
    HAS_ARTIFACT,
)

from .predicates import (
    IS_MONSTER,
    IS_SPELL,
    DAMAGED,
    HAS_KEYWORD,
    HAS_STATUS,
    HAS_TRIBE,
    GENERATED,
    NON_GENERATED,
    GENERATED_BY,
    SPENT_GOLD_LAST_TURN,
    SPENT_GOLD_LAST_TURN_ON_SPELLS,
    TOKEN,
    NON_TOKEN,
    DT,
    NON_DT,
)

from .transforms import (
    RANDOM,
    MIN,
    MAX,
    LEFTMOST,
    RIGHTMOST,
    DISTINCT,
    SORT_BY,
    GENERATE,
    COPY,
    EXACT_COPY,
)

from .discovery import DISCOVER

from .vars import (
    Var,
    VAR,
    CHOICE_SELECTED,
    CHOICE_NOT_SELECTED,
)

from .macros import (
    Program,
    Switch,
    SwitchPiece,

    NEXT_LOST_SOUL,
)


# Card keywords
CHARGE = CardKeyword.CHARGE
HASTE = CardKeyword.HASTE
TAUNT = CardKeyword.TAUNT
KR = CardKeyword.KR
CANDY = CardKeyword.CANDY
ARMOR = CardKeyword.ARMOR
TRANSPARENCY = CardKeyword.TRANSPARENCY
DISARMED = CardKeyword.DISARMED
INVULNERABLE = CardKeyword.INVULNERABLE
SILENCED = CardKeyword.SILENCED
WANTED = CardKeyword.WANTED
DARKSPAWN = CardKeyword.DARKSPAWN

# Abilities
MAGIC = Ability.MAGIC
SYNERGY = Ability.SYNERGY
DUST = Ability.DUST
DELAY = Ability.DELAY
TURN_START = Ability.TURN_START
TURN_END = Ability.TURN_END
SHOCK = Ability.SHOCK
SUPPORT = Ability.SUPPORT
TURBO = Ability.TURBO
BULLSEYE = Ability.BULLSEYE


__all__ = [
    # Card keywords
    'CHARGE', 'HASTE', 'TAUNT', 'KR', 'CANDY', 'ARMOR', 'TRANSPARENCY', 'DISARMED', 'INVULNERABLE',
    'SILENCED', 'WANTED', 'DARKSPAWN',

    # Abilities
    'MAGIC', 'SYNERGY', 'DUST', 'DELAY', 'TURN_START', 'TURN_END',
    'SHOCK', 'SUPPORT', 'TURBO', 'BULLSEYE',

    # Core
    'TargetSelector',
    'Predicate',
    'Transform',
    'ValueExpr',
    'TargetingError',
    'NoTargetsError',
    'AmbiguousTargetError',

    # Selectors
    'SELF', 'TARGET', 'KILLER', 'ATTACKER',
    'YOU', 'CONTROLLER', 'OPPONENT', 'TURN_PLAYER',

    'BOARD', 'HAND', 'DECK', 'DUSTPILE', 'ERASED',
    'OPPONENT_BOARD', 'OPPONENT_HAND', 'OPPONENT_DECK', 'OPPONENT_DUSTPILE', 'OPPONENT_ERASED',

    'ALLY_MONSTERS', 'ENEMY_MONSTERS',
    'ALLIES', 'ENEMIES',

    'LEFT', 'RIGHT', 'ADJACENT', 'FRONT',
    'LEFT_OF', 'RIGHT_OF',

    'LEFT_IN_HAND', 'RIGHT_IN_HAND', 'ADJACENT_IN_HAND',

    'BOARD_OF', 'HAND_OF', 'DECK_OF', 'DUSTPILE_OF', 'ERASED_OF',
    'CONTROLLER_OF', 'OPPONENT_OF',

    'CARD_LIBRARY', 'CARD_BY_NAME',

    # Values
    'ID', 'TEMPLATE_ID',
    'COST', 'RARITY',
    'ATTACK', 'HP', 'MAX_HP',
    'CREATOR_ID',
    'BASE_COST', 'BASE_ATTACK', 'BASE_HP',
    'COUNT',
    'EMPTY_SLOTS',
    'CLAMP', 'LEAST', 'GREATEST',
    'SYNERGY_TRIGGERED',
    'HAS_ARTIFACT',

    # Predicates
    'IS_MONSTER',
    'IS_SPELL',
    'DAMAGED',
    'HAS_KEYWORD',
    'HAS_STATUS',
    'HAS_TRIBE',
    'GENERATED',
    'NON_GENERATED',
    'GENERATED_BY',
    'SPENT_GOLD_LAST_TURN',
    'SPENT_GOLD_LAST_TURN_ON_SPELLS',
    'TOKEN',
    'NON_TOKEN',
    'DT',
    'NON_DT',

    # Transforms
    'RANDOM',
    'MIN',
    'MAX',
    'LEFTMOST',
    'RIGHTMOST',
    'DISTINCT',
    'SORT_BY',
    'GENERATE',
    'COPY',
    'EXACT_COPY',

    # Discovery
    'DISCOVER',

    # Variables
    'Var',
    'VAR',
    'CHOICE_SELECTED',
    'CHOICE_NOT_SELECTED',

    # Macros
    'Program',
    'Switch',
    'SwitchPiece',

    'NEXT_LOST_SOUL',
]
