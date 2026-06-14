from dataclasses import dataclass
from typing import Any, Literal, TYPE_CHECKING

from cards import Card, Monster, CardZone
from cards.library import LIBRARY
from snapshots import MonsterSnapshot

from .core import TargetSelector, TargetingError, resolve_selector_value

if TYPE_CHECKING:
    from actions import ActionContext


# --------------------
# Context selectors
# --------------------

@dataclass(frozen=True, slots=True, eq=False)
class SelfSelector(TargetSelector):
    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        return [ctx.source]

    def __repr__(self) -> str:
        return "SELF"


@dataclass(frozen=True, slots=True, eq=False)
class EnvSelector(TargetSelector):
    key: str

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        try:
            value = ctx.env[self.key]
        except KeyError:
            raise TargetingError(f"ctx.env['{self.key}'] is not set")

        return resolve_selector_value(value, ctx=ctx, **kwargs)

    def __repr__(self) -> str:
        return self.key.upper()


@dataclass(frozen=True, slots=True, eq=False)
class YouSelector(TargetSelector):
    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        player_id = ctx.source.controller_id
        return [ctx.game.player(player_id)]

    def __repr__(self) -> str:
        return "YOU"


@dataclass(frozen=True, slots=True, eq=False)
class OpponentSelector(TargetSelector):
    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        player_id = ctx.source.controller_id
        return [ctx.game.player(player_id).opponent]

    def __repr__(self) -> str:
        return "OPPONENT"


@dataclass(frozen=True, slots=True, eq=False)
class TurnPlayerSelector(TargetSelector):
    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        return [ctx.game.turn_player]

    def __repr__(self) -> str:
        return "TURN_PLAYER"


# ------------------------
# Entity player selectors
# ------------------------

@dataclass(frozen=True, slots=True, eq=False)
class EntityControllerSelector(TargetSelector):
    inner: TargetSelector

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        entity = self.inner.eval_optional_one(ctx=ctx, **kwargs)
        if entity is None:
            return []

        player_id = entity.controller_id
        return [ctx.game.player(player_id)]

    def __repr__(self) -> str:
        return f"CONTROLLER_OF({self.inner!r})"


@dataclass(frozen=True, slots=True, eq=False)
class EntityOpponentSelector(TargetSelector):
    inner: TargetSelector

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        player = CONTROLLER_OF(self.inner).eval_optional_one(ctx=ctx, **kwargs)
        if player is None:
            return []

        return [player.opponent]

    def __repr__(self) -> str:
        return f"OPPONENT_OF({self.inner!r})"


def CONTROLLER_OF(x: TargetSelector) -> EntityControllerSelector:
    return EntityControllerSelector(x)


def OPPONENT_OF(x: TargetSelector) -> EntityOpponentSelector:
    return EntityOpponentSelector(x)


# --------------------
# Zone selectors
# --------------------

@dataclass(frozen=True, slots=True, eq=False)
class ZoneSelector(TargetSelector):
    zone: CardZone
    player: TargetSelector

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        player = self.player.eval_optional_one(ctx=ctx, **kwargs)
        if player is None:
            return []

        container = getattr(player, self.zone.value)
        return container.cards.copy()

    def __repr__(self) -> str:
        return f"{self.zone.value.upper()}({self.player!r})"


def BOARD_OF(player: TargetSelector) -> ZoneSelector:
    return ZoneSelector(CardZone.BOARD, player)


def HAND_OF(player: TargetSelector) -> ZoneSelector:
    return ZoneSelector(CardZone.HAND, player)


def DECK_OF(player: TargetSelector) -> ZoneSelector:
    return ZoneSelector(CardZone.DECK, player)


def DUSTPILE_OF(player: TargetSelector) -> ZoneSelector:
    return ZoneSelector(CardZone.DUSTPILE, player)


def ERASED_OF(player: TargetSelector) -> ZoneSelector:
    return ZoneSelector(CardZone.ERASED, player)


# -------------------------
# Board-relative selectors
# -------------------------

@dataclass(frozen=True, slots=True, eq=False)
class RelativeBoardSelector(TargetSelector):
    inner: TargetSelector
    offset: int
    opponent_side: bool = False

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        monster = self.inner.eval_optional_one(ctx=ctx, **kwargs)
        if monster is None:
            return []

        if not isinstance(monster, (Monster, MonsterSnapshot)):
            raise TargetingError(f"RelativeBoardSelector expects Monster/MonsterSnapshot, got {type(monster).__name__}: {monster!r}")

        if monster.zone is not CardZone.BOARD:
            return []

        player = ctx.game.player(monster.controller_id)
        if self.opponent_side:
            player = player.opponent

        pos = monster.pos + self.offset
        if not (0 <= pos < player.board.MAX_CARDS):
            return []

        monster = player.board[pos]
        return [monster] if monster is not None else []

    def __repr__(self) -> str:
        if self.opponent_side and self.offset == 0:
            return f"FRONT({self.inner!r})"

        if self.offset == -1:
            return f"LEFT({self.inner!r})"

        if self.offset == +1:
            return f"RIGHT({self.inner!r})"

        return f"RelativeBoardSelector({self.inner!r}, offset={self.offset}, opponent_side={self.opponent_side})"


def LEFT(x: TargetSelector) -> RelativeBoardSelector:
    return RelativeBoardSelector(x, offset=-1, opponent_side=False)


def RIGHT(x: TargetSelector) -> RelativeBoardSelector:
    return RelativeBoardSelector(x, offset=+1, opponent_side=False)


def ADJACENT(x: TargetSelector) -> TargetSelector:
    return LEFT(x) | RIGHT(x)


def FRONT(x: TargetSelector) -> RelativeBoardSelector:
    return RelativeBoardSelector(x, offset=0, opponent_side=True)


@dataclass(frozen=True, slots=True, eq=False)
class RelativeBoardRangeSelector(TargetSelector):
    inner: TargetSelector
    direction: Literal['left', 'right']

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        monster = self.inner.eval_optional_one(ctx=ctx, **kwargs)
        if monster is None:
            return []

        if not isinstance(monster, (Monster, MonsterSnapshot)):
            raise TargetingError(f"RelativeBoardRangeSelector expects Monster/MonsterSnapshot, got {type(monster).__name__}: {monster!r}")

        if monster.zone is not CardZone.BOARD:
            return []

        player = ctx.game.player(monster.controller_id)

        if self.direction == 'left':
            slots = range(0, monster.pos)
        else:
            slots = range(monster.pos + 1, player.board.MAX_CARDS)

        result = []
        for index in slots:
            m = player.board[index]
            if m is not None:
                result.append(m)

        return result

    def __repr__(self) -> str:
        return f"{'LEFT_OF' if self.direction == 'left' else 'RIGHT_OF'}({self.inner!r})"


def LEFT_OF(x: TargetSelector) -> TargetSelector:
    return RelativeBoardRangeSelector(x, direction='left')


def RIGHT_OF(x: TargetSelector) -> TargetSelector:
    return RelativeBoardRangeSelector(x, direction='right')


# ------------------------
# Hand-relative selectors
# ------------------------

@dataclass(frozen=True, slots=True, eq=False)
class RelativeHandSelector(TargetSelector):
    inner: TargetSelector
    offset: int

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        card = self.inner.eval_optional_one(ctx=ctx, **kwargs)
        if card is None:
            return []

        if not isinstance(card, Card):
            raise TargetingError(f"RelativeHandSelector expects Card, got {type(card).__name__}: {card!r}")

        player = ctx.game.player(card.controller_id)
        cards = player.hand.cards

        try:
            index = cards.index(card)
        except ValueError:
            return []

        target_index = index + self.offset
        if 0 <= target_index < len(cards):
            return [cards[target_index]]

        return []

    def __repr__(self) -> str:
        if self.offset == -1:
            return f"LEFT_IN_HAND({self.inner!r})"
        if self.offset == +1:
            return f"RIGHT_IN_HAND({self.inner!r})"

        return f"RelativeHandSelector({self.inner!r}, offset={self.offset})"


def LEFT_IN_HAND(x: TargetSelector) -> RelativeHandSelector:
    return RelativeHandSelector(x, offset=-1)


def RIGHT_IN_HAND(x: TargetSelector) -> RelativeHandSelector:
    return RelativeHandSelector(x, offset=+1)


def ADJACENT_IN_HAND(x: TargetSelector) -> TargetSelector:
    return LEFT_IN_HAND(x) | RIGHT_IN_HAND(x)


# --------------------
# Library selectors
# --------------------

@dataclass(frozen=True, slots=True, eq=False)
class CardLibrarySelector(TargetSelector):
    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        return list(LIBRARY._by_id.values())  # TODO cache

    def __repr__(self) -> str:
        return "CARD_LIBRARY"


@dataclass(frozen=True, slots=True, eq=False)
class CardByNameSelector(TargetSelector):
    name: str

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        return [LIBRARY.get_by_name(self.name)]

    def __repr__(self) -> str:
        return f"CARD_BY_NAME({self.name!r})"


def CARD_BY_NAME(name: str) -> CardByNameSelector:
    return CardByNameSelector(name=name)


@dataclass(frozen=True, slots=True, eq=False)
class NextLostSoulSelector(TargetSelector):
    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        lost_soul_card_names = ("LostAlphys", "LostPapyrus", "LostUndyne", "LostToriel", "LostAsgore", "LostSans")
        player_id = ctx.source.controller_id
        player = ctx.game.player(player_id)

        if player.next_lost_soul is not None:
            card = LIBRARY.get_by_name(lost_soul_card_names[player.next_lost_soul])
            player.next_lost_soul += 1
            if player.next_lost_soul >= len(lost_soul_card_names):
                player.next_lost_soul = 0

        else:
            card = LIBRARY.get_by_name(ctx.game.rng.choice(lost_soul_card_names))

        return [card]

    def __repr__(self) -> str:
        return "NEXT_LOST_SOUL"


SELF = SelfSelector()
TARGET = EnvSelector('target')
KILLER = EnvSelector('killer')
ATTACKER = EnvSelector('attacker')

YOU = YouSelector()
CONTROLLER = YOU
OPPONENT = OpponentSelector()
TURN_PLAYER = TurnPlayerSelector()

BOARD = ZoneSelector(CardZone.BOARD, YOU)
HAND = ZoneSelector(CardZone.HAND, YOU)
DECK = ZoneSelector(CardZone.DECK, YOU)
DUSTPILE = ZoneSelector(CardZone.DUSTPILE, YOU)
ERASED = ZoneSelector(CardZone.ERASED, YOU)

OPPONENT_BOARD = ZoneSelector(CardZone.BOARD, OPPONENT)
OPPONENT_HAND = ZoneSelector(CardZone.HAND, OPPONENT)
OPPONENT_DECK = ZoneSelector(CardZone.DECK, OPPONENT)
OPPONENT_DUSTPILE = ZoneSelector(CardZone.DUSTPILE, OPPONENT)
OPPONENT_ERASED = ZoneSelector(CardZone.ERASED, OPPONENT)

ALLY_MONSTERS = BOARD
ENEMY_MONSTERS = OPPONENT_BOARD

ALLIES = YOU | ALLY_MONSTERS
ENEMIES = OPPONENT | ENEMY_MONSTERS

CARD_LIBRARY = CardLibrarySelector()
