from deltacards.actions import results as _action_results
from deltacards.actions import standard as _action_standard

from deltacards.actions.results import *
from deltacards.actions.standard import *

from deltacards.engine.effects import Check, For, ForEach, StepResult
from deltacards.model.cards import Card, Monster, Spell, card
from deltacards.model.entity import Entity, on_event
from deltacards.model.enums import (
    Ability,
    CardKeyword,
    CardRarity,
    CardStatusId,
    CardZone,
    DamageKind,
    PlayerId,
    Tribe,
)

from deltacards.dsl.core import (
    AmbiguousTargetError,
    NoTargetsError,
    Predicate,
    TargetSelector,
    TargetingError,
    Transform,
    ValueExpr,
)
from deltacards.dsl.discovery import DISCOVER
from deltacards.dsl.macros import NEXT_LOST_SOUL, Program, Switch, SwitchPiece
from deltacards.dsl.predicates import (
    DAMAGED,
    DT,
    GENERATED,
    GENERATED_BY,
    HAS_KEYWORD,
    HAS_STATUS,
    HAS_TRIBE,
    IS_MONSTER,
    IS_SPELL,
    NON_DT,
    NON_GENERATED,
    NON_TOKEN,
    SPENT_GOLD_LAST_TURN,
    SPENT_GOLD_LAST_TURN_ON_SPELLS,
    TOKEN,
)
from deltacards.dsl.selectors import (
    ADJACENT,
    ADJACENT_IN_HAND,
    ALLIES,
    ALLY_MONSTERS,
    ATTACKER,
    BOARD,
    BOARD_OF,
    CARD_BY_NAME,
    CARD_LIBRARY,
    CONTROLLER,
    CONTROLLER_OF,
    DECK,
    DECK_OF,
    DUSTPILE,
    DUSTPILE_OF,
    ENEMIES,
    ENEMY_MONSTERS,
    ERASED,
    ERASED_OF,
    FRONT,
    HAND,
    HAND_OF,
    KILLER,
    LEFT,
    LEFT_IN_HAND,
    LEFT_OF,
    OPPONENT,
    OPPONENT_BOARD,
    OPPONENT_DECK,
    OPPONENT_DUSTPILE,
    OPPONENT_ERASED,
    OPPONENT_HAND,
    OPPONENT_OF,
    RIGHT,
    RIGHT_IN_HAND,
    RIGHT_OF,
    SELF,
    TARGET,
    TURN_PLAYER,
    YOU,
)
from deltacards.dsl.transforms import (
    COPY,
    DISTINCT,
    EXACT_COPY,
    GENERATE,
    LEFTMOST,
    MAX,
    MIN,
    RANDOM,
    RIGHTMOST,
    SORT_BY,
)
from deltacards.dsl.values import (
    ATTACK,
    BASE_ATTACK,
    BASE_COST,
    BASE_HP,
    CLAMP,
    COST,
    COUNT,
    CREATOR_ID,
    EMPTY_SLOTS,
    GREATEST,
    HAS_ARTIFACT,
    HP,
    ID,
    LEAST,
    MAX_HP,
    RARITY,
    SYNERGY_TRIGGERED,
    TEMPLATE_ID,
)
from deltacards.dsl.vars import CHOICE_NOT_SELECTED, CHOICE_SELECTED, VAR, Var

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

    # Effects
    'Check', 'For', 'ForEach', 'StepResult',

    # Cards
    'Card', 'Monster', 'Spell', 'card',

    # Entity
    'Entity', 'on_event',

    # Enums
    'Ability',
    'CardKeyword',
    'CardRarity',
    'CardStatusId',
    'CardZone',
    'DamageKind',
    'PlayerId',
    'Tribe',

    *_action_results.__all__,
    *_action_standard.__all__,
]
