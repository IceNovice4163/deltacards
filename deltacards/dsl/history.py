from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING

from deltacards.actions.results import (
    AttackDeclaredResult,
    AttackResolvedResult,
    AbilityTriggeredResult,
    ActionResult,
    CardDrawnResult,
    CardPlayedResult,
    EntityHealedResult,
    GoldSpentResult,
    MonsterKilledResult,
    SpellCastResult,
)
from deltacards.dsl.aggregates import SUM
from deltacards.dsl.core import Predicate, TargetSelector, TargetingError, ValueExpr, to_value
from deltacards.dsl.inspection import (
    _MISSING,
    attr_of,
    card_type_of,
    controller_id_of,
    soul_id_of,
    source_id_of,
    target_id_of,
    killer_id_of,
    attacker_id_of,
    defender_id_of,
)
from deltacards.dsl.selectors import YOU
from deltacards.dsl.values import TEMPLATE_ID
from deltacards.model.entity import Entity
from deltacards.model.enums import Ability, CardType, KillCause, PlayerId
from deltacards.model.player import Player
from deltacards.model.types import GoldSpendReason

if TYPE_CHECKING:
    from deltacards.actions.standard import ActionContext


_NO_MATCH = object()


# --------------------
# Helpers
# --------------------

def _result_turn_key(result: ActionResult) -> tuple[int, PlayerId]:
    return result.turn, result.turn_player_id


def _current_turn_key(ctx: 'ActionContext') -> tuple[int, PlayerId] | None:
    if ctx.game.turn_player is None:
        return None

    return ctx.game.turn, ctx.game.turn_player.id


def _last_completed_turn_key_of(ctx: 'ActionContext', player_id: PlayerId) -> tuple[int, PlayerId] | None:
    """
    Return the latest completed "half-turn" belonging to `player_id`.

    If `player_id` is the current turn player, the current turn is still in
    progress and does not count as "last turn" yet.
    """
    players = list(ctx.game.players.values())

    try:
        turn_player_index = players.index(ctx.game.turn_player)
    except ValueError:
        return None

    target_index = None
    for i, player in enumerate(players):
        if player.id == player_id:
            target_index = i
            break

    if target_index is None:
        return None

    if player_id == ctx.game.turn_player.id:
        turn_number = ctx.game.turn - 1
    elif target_index < turn_player_index:
        turn_number = ctx.game.turn
    else:
        turn_number = ctx.game.turn - 1

    if turn_number < 1:
        return None

    return turn_number, player_id


def _resolve_player_id(spec: Any, ctx: 'ActionContext', **kwargs) -> PlayerId | _NO_MATCH | None:
    if spec is None:
        return None

    if isinstance(spec, PlayerId):
        return spec

    if isinstance(spec, Player):
        return spec.id

    if isinstance(spec, TargetSelector):
        player = spec.eval_optional_one(ctx=ctx, **kwargs)
        if player is None:
            return _NO_MATCH

        if not isinstance(player, Player):
            raise TargetingError(f"Expected player selector, got {type(player).__name__}: {player!r}")

        return player.id

    raise TypeError(f"Invalid player type {type(spec).__name__}: {spec!r}")


def _resolve_entity_id(spec: Any, ctx: 'ActionContext', **kwargs) -> PlayerId | int | _NO_MATCH | None:
    if spec is None:
        return None

    if isinstance(spec, int):
        return spec

    if isinstance(spec, PlayerId):
        return spec

    if isinstance(spec, Entity):
        return spec.id

    if isinstance(spec, TargetSelector):
        entity = spec.eval_optional_one(ctx=ctx, **kwargs)
        if entity is None:
            return _NO_MATCH

        if not isinstance(entity, Entity):
            raise TargetingError(f"Expected entity selector, got {type(entity).__name__}: {entity!r}")

        return entity.id

    raise TypeError(f"Invalid entity type {type(spec).__name__}: {spec!r}")


# --------------------
# History scopes
# --------------------

class HistoryScope(ABC):
    __slots__ = ()

    def __bool__(self) -> bool:
        raise TypeError("Cannot evaluate HistoryScope to boolean; check DSL syntax")

    def __and__(self, other: 'HistoryScope') -> 'HistoryScope':
        if not isinstance(other, HistoryScope):
            return NotImplemented

        return AndHistoryScope(self, other)

    def __or__(self, other: 'HistoryScope') -> 'HistoryScope':
        if not isinstance(other, HistoryScope):
            return NotImplemented

        return OrHistoryScope(self, other)

    def __invert__(self) -> 'HistoryScope':
        return NotHistoryScope(self)

    @abstractmethod
    def resolve(self, ctx: 'ActionContext', **kwargs) -> Callable[[ActionResult], bool]:
        pass


@dataclass(frozen=True, slots=True, eq=False)
class AndHistoryScope(HistoryScope):
    left: HistoryScope
    right: HistoryScope

    def resolve(self, ctx: 'ActionContext', **kwargs) -> Callable[[ActionResult], bool]:
        left = self.left.resolve(ctx=ctx, **kwargs)
        right = self.right.resolve(ctx=ctx, **kwargs)
        return lambda result: left(result) and right(result)

    def __repr__(self) -> str:
        return f"({self.left!r} & {self.right!r})"


@dataclass(frozen=True, slots=True, eq=False)
class OrHistoryScope(HistoryScope):
    left: HistoryScope
    right: HistoryScope

    def resolve(self, ctx: 'ActionContext', **kwargs) -> Callable[[ActionResult], bool]:
        left = self.left.resolve(ctx=ctx, **kwargs)
        right = self.right.resolve(ctx=ctx, **kwargs)
        return lambda result: left(result) or right(result)

    def __repr__(self) -> str:
        return f"({self.left!r} | {self.right!r})"


@dataclass(frozen=True, slots=True, eq=False)
class NotHistoryScope(HistoryScope):
    inner: HistoryScope

    def resolve(self, ctx: 'ActionContext', **kwargs) -> Callable[[ActionResult], bool]:
        inner = self.inner.resolve(ctx=ctx, **kwargs)
        return lambda result: not inner(result)

    def __repr__(self) -> str:
        return f"(~{self.inner!r})"


@dataclass(frozen=True, slots=True, eq=False)
class AllHistoryScope(HistoryScope):
    def resolve(self, ctx: 'ActionContext', **kwargs) -> Callable[[ActionResult], bool]:
        return lambda result: True

    def __repr__(self) -> str:
        return "THIS_GAME"


@dataclass(frozen=True, slots=True, eq=False)
class CurrentTurnScope(HistoryScope):
    def resolve(self, ctx: 'ActionContext', **kwargs) -> Callable[[ActionResult], bool]:
        key = _current_turn_key(ctx)
        if key is None:
            return lambda result: False

        return lambda result: _result_turn_key(result) == key

    def __repr__(self) -> str:
        return "THIS_TURN"


@dataclass(frozen=True, slots=True, eq=False)
class LastTurnOfPlayerScope(HistoryScope):
    player: Any

    def resolve(self, ctx: 'ActionContext', **kwargs) -> Callable[[ActionResult], bool]:
        player_id = _resolve_player_id(self.player, ctx=ctx, **kwargs)
        if player_id is _NO_MATCH:
            return lambda result: False

        key = _last_completed_turn_key_of(ctx, player_id)
        if key is None:
            return lambda result: False

        return lambda result: _result_turn_key(result) == key

    def __repr__(self) -> str:
        return f"LAST_TURN_OF({self.player!r})"


THIS_GAME = AllHistoryScope()
THIS_TURN = CurrentTurnScope()


def LAST_TURN_OF(player: Any) -> HistoryScope:
    return LastTurnOfPlayerScope(player)


# --------------------
# History selectors
# --------------------

@dataclass(frozen=True, slots=True, eq=False)
class HistorySelector(TargetSelector):
    result_type: type[ActionResult]
    scope: HistoryScope = THIS_GAME

    player: Any | None = None
    controller: Any | None = None
    turn_player: Any | None = None

    source: Any | None = None
    target: Any | None = None
    killer: Any | None = None
    attacker: Any | None = None
    defender: Any | None = None

    ability: Ability | None = None

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        scope_test = self.scope.resolve(ctx=ctx, **kwargs)

        player_id = _resolve_player_id(self.player, ctx=ctx, **kwargs)
        controller_id = _resolve_player_id(self.controller, ctx=ctx, **kwargs)
        turn_player_id = _resolve_player_id(self.turn_player, ctx=ctx, **kwargs)

        source_id = _resolve_entity_id(self.source, ctx=ctx, **kwargs)
        target_id = _resolve_entity_id(self.target, ctx=ctx, **kwargs)
        killer_id = _resolve_entity_id(self.killer, ctx=ctx, **kwargs)
        attacker_id = _resolve_entity_id(self.attacker, ctx=ctx, **kwargs)
        defender_id = _resolve_entity_id(self.defender, ctx=ctx, **kwargs)

        if any(
            value is _NO_MATCH
            for value in (
                player_id,
                controller_id,
                turn_player_id,
                source_id,
                target_id,
                killer_id,
                attacker_id,
                defender_id,
            )
        ):
            return []

        check_player = player_id is not None
        check_controller = controller_id is not None
        check_turn_player = turn_player_id is not None
        check_source = source_id is not None
        check_target = target_id is not None
        check_killer = killer_id is not None
        check_attacker = attacker_id is not None
        check_defender = defender_id is not None
        check_ability = self.ability is not None

        result = []
        for entry in ctx.game.log_by_type[self.result_type]:
            if not scope_test(entry):
                continue

            if check_player and entry.history_player_id != player_id:
                continue

            if check_controller and controller_id_of(entry, default=_MISSING) != controller_id:
                continue

            if check_turn_player and entry.turn_player_id != turn_player_id:
                continue

            if check_source and source_id_of(entry, default=_MISSING) != source_id:
                continue

            if check_target and target_id_of(entry, default=_MISSING) != target_id:
                continue

            if check_killer and killer_id_of(entry, default=_MISSING) != killer_id:
                continue

            if check_attacker and attacker_id_of(entry, default=_MISSING) != attacker_id:
                continue

            if check_defender and defender_id_of(entry, default=_MISSING) != defender_id:
                continue

            if check_ability and entry.ability is not self.ability:
                continue

            result.append(entry)

        return result

    def __repr__(self) -> str:
        args = [self.result_type.__name__]

        if self.scope is not THIS_GAME:
            args.append(f"scope={self.scope!r}")

        for name in ('player', 'controller', 'turn_player', 'source', 'target', 'killer', 'attacker', 'defender'):
            value = getattr(self, name)
            if value is not None:
                args.append(f"{name}={value!r}")

        return f"HISTORY({', '.join(args)})"


def CARDS_PLAYED(player: Any | None = YOU, *, scope: HistoryScope = THIS_GAME) -> HistorySelector:
    return HistorySelector(CardPlayedResult, player=player, scope=scope)


def CARDS_DRAWN(player: Any | None = YOU, *, scope: HistoryScope = THIS_GAME) -> HistorySelector:
    return HistorySelector(CardDrawnResult, player=player, scope=scope)


def SPELLS_CAST(player: Any | None = YOU, *, scope: HistoryScope = THIS_GAME) -> HistorySelector:
    # Explicit `is_played == True` check (spells count as cast only if played)
    return HistorySelector(SpellCastResult, player=player, scope=scope) & (HistoryAttrValue('is_played') == True)


def ATTACKS_DECLARED(
    *,
    attacker_controller: Any | None = YOU,
    scope: HistoryScope = THIS_GAME,
) -> HistorySelector:
    return HistorySelector(
        AttackDeclaredResult,
        controller=attacker_controller,
        scope=scope,
    )


def ATTACKS_RESOLVED(
    *,
    attacker_controller: Any | None = YOU,
    scope: HistoryScope = THIS_GAME,
) -> HistorySelector:
    return HistorySelector(
        AttackResolvedResult,
        controller=attacker_controller,
        scope=scope,
    )


def HEALING_DONE(
    *,
    controller: Any | None = YOU,
    scope: HistoryScope = THIS_GAME,
) -> HistorySelector:
    """
    Select healing results whose healed target is the selected Player or one
    of that Player's controlled Monsters.
    """
    return HistorySelector(
        EntityHealedResult,
        controller=controller,
        scope=scope,
    )


def GOLD_SPENT(
    player: Any | None = YOU,
    *,
    scope: HistoryScope = THIS_GAME,
    reason: GoldSpendReason | None = None,
) -> TargetSelector:
    selector = HistorySelector(GoldSpentResult, scope=scope, player=player)

    if reason is not None:
        selector = selector & (REASON == reason)

    return selector


def MONSTERS_DIED(
    *,
    scope: HistoryScope = THIS_GAME,
    controller: Any | None = None,
    killer: Any | None = None,
    turn_player: Any | None = None,
) -> HistorySelector:
    return HistorySelector(
        MonsterKilledResult,
        scope=scope,
        controller=controller,
        killer=killer,
        turn_player=turn_player,
    )


def ABILITY_TRIGGERS(
    *,
    scope: HistoryScope = THIS_GAME,
    controller: Any | None = None,
    source: Any | None = None,
    ability: Any | None = None,
) -> HistorySelector:
    return HistorySelector(
        AbilityTriggeredResult,
        scope=scope,
        controller=controller,
        source=source,
        ability=ability,
    )


# --------------------
# Value expressions
# --------------------

@dataclass(frozen=True, slots=True, eq=False)
class HistoryAttrValue(ValueExpr):
    attr: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        if entity is None:
            raise TargetingError(f"{self.attr.upper()} requires a candidate history entry")

        value = attr_of(entity, self.attr, default=_MISSING)
        if value is _MISSING:
            raise TargetingError(f"{self.attr.upper()} is not available on {type(entity).__name__}")

        return value

    def __repr__(self) -> str:
        return self.attr.upper()


CARD_ID = HistoryAttrValue('card_id')
MONSTER_ID = HistoryAttrValue('monster_id')

AMOUNT = HistoryAttrValue('amount')
HEALED_AMOUNT = HistoryAttrValue('amount')

REASON = HistoryAttrValue('reason')

ATTACKER_ID = HistoryAttrValue('attacker_id')
DEFENDER_ID = HistoryAttrValue('defender_id')

KILL_CAUSE = HistoryAttrValue('cause')

HAS_NEED_CONDITION = HistoryAttrValue('has_need_condition')
NEED_FULFILLED = HistoryAttrValue('need_fulfilled')

TEMPLATE_NAME = HistoryAttrValue('template_name')

CARD_SOUL = HistoryAttrValue('soul_id')


@dataclass(frozen=True, slots=True, eq=False)
class PlayerSoulValue(ValueExpr):
    player: TargetSelector

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        player = self.player.eval_one(ctx=ctx, **kwargs)
        if not isinstance(player, Player):
            raise TargetingError(f"PLAYER_SOUL expects a player selector, got {type(player).__name__}: {player!r}")

        return player.starting_soul_id

    def __repr__(self) -> str:
        return f"PLAYER_SOUL({self.player!r})"


def PLAYER_SOUL(player: TargetSelector = YOU) -> PlayerSoulValue:
    return PlayerSoulValue(player=player)


# --------------------
# Predicates
# --------------------

@dataclass(frozen=True, slots=True, eq=False)
class InHistoryPredicate(Predicate):
    history: TargetSelector
    candidate_key: ValueExpr
    history_key: ValueExpr

    def _history_values(self, ctx: 'ActionContext', **kwargs) -> tuple[Any]:
        # maybe there is a better way?
        cache_key = (
            'history.InHistoryPredicate',
            id(self),
            len(ctx.game.log),
        )

        try:
            return ctx.cache[cache_key]
        except KeyError:
            pass

        values = tuple(
            self.history_key.eval(ctx=ctx, entity=entry, **kwargs)
            for entry in self.history.eval(ctx=ctx, **kwargs)
        )
        ctx.cache[cache_key] = values
        return values

    def test(self, entity: Any, ctx: 'ActionContext', **kwargs) -> bool:
        candidate_value = self.candidate_key.eval(ctx=ctx, entity=entity, **kwargs)
        return candidate_value in self._history_values(ctx=ctx, **kwargs)

    def __repr__(self) -> str:
        return f"IN_HISTORY({self.history!r}, candidate_key={self.candidate_key!r}, history_key={self.history_key!r})"


def IN_HISTORY(
    history: TargetSelector,
    *,
    candidate_key: Any | None = None,
    history_key: Any | None = None,
) -> InHistoryPredicate:
    return InHistoryPredicate(
        history=history,
        candidate_key=TEMPLATE_ID if candidate_key is None else to_value(candidate_key),
        history_key=TEMPLATE_ID if history_key is None else to_value(history_key),
    )


@dataclass(frozen=True, slots=True, eq=False)
class IsCombatKillPredicate(Predicate):
    def test(self, entity: Any, ctx: 'ActionContext', **kwargs) -> bool:
        cause = attr_of(entity, 'cause', default=None)
        return cause is KillCause.COMBAT

    def __repr__(self) -> str:
        return "IS_COMBAT_KILL"


IS_COMBAT_KILL = IsCombatKillPredicate()


@dataclass(frozen=True, slots=True, eq=False)
class KilledByMonsterPredicate(Predicate):
    def test(self, entity: Any, ctx: 'ActionContext', **kwargs) -> bool:
        killer = attr_of(entity, 'killer', default=None)
        return card_type_of(killer, default=None) is CardType.MONSTER

    def __repr__(self) -> str:
        return "KILLED_BY_MONSTER"


KILLED_BY_MONSTER = KilledByMonsterPredicate()


@dataclass(frozen=True, slots=True, eq=False)
class OfSoulPredicate(Predicate):
    soul: ValueExpr

    def test(self, entity: Any, ctx: 'ActionContext', **kwargs) -> bool:
        actual = soul_id_of(entity, default=_MISSING)
        if actual is _MISSING:
            return False

        expected = self.soul.eval(ctx=ctx, entity=entity, **kwargs)
        return actual == expected

    def __repr__(self) -> str:
        return f"OF_SOUL({self.soul!r})"


def OF_SOUL(soul: Any) -> OfSoulPredicate:
    return OfSoulPredicate(to_value(soul))


@dataclass(frozen=True, slots=True, eq=False)
class AnotherSoulThanPredicate(Predicate):
    player: TargetSelector

    def test(self, entity: Any, ctx: 'ActionContext', **kwargs) -> bool:
        actual = soul_id_of(entity, default=_MISSING)
        if actual is _MISSING:
            return False

        expected = PLAYER_SOUL(self.player).eval(ctx=ctx, entity=entity, **kwargs)
        return actual != expected


def ANOTHER_SOUL_THAN(player: TargetSelector = YOU) -> Predicate:
    return AnotherSoulThanPredicate(player)


# --------------------
# Gold helpers
# --------------------

def SPENT_GOLD_AMOUNT(
    *,
    player: Any | None = YOU,
    scope: HistoryScope = THIS_GAME,
    reason: GoldSpendReason | None = None,
) -> ValueExpr:
    return SUM(
        GOLD_SPENT(
            player=player,
            scope=scope,
            reason=reason,
        ),
        AMOUNT,
    )


def SPENT_GOLD_LAST_TURN_OF(player: Any) -> ValueExpr:
    return SPENT_GOLD_AMOUNT(player=player, scope=LAST_TURN_OF(player))


def SPENT_GOLD_LAST_TURN_ON_SPELLS_OF(player: Any) -> ValueExpr:
    return SPENT_GOLD_AMOUNT(player=player, scope=LAST_TURN_OF(player), reason='play_spell')


SPENT_GOLD_THIS_TURN = SPENT_GOLD_AMOUNT(player=YOU, scope=THIS_TURN)
SPENT_GOLD_ON_SPELLS_THIS_TURN = SPENT_GOLD_AMOUNT(player=YOU, scope=THIS_TURN, reason='play_spell')

SPENT_GOLD_LAST_TURN = SPENT_GOLD_LAST_TURN_OF(YOU)
SPENT_GOLD_ON_SPELLS_LAST_TURN = SPENT_GOLD_LAST_TURN_ON_SPELLS_OF(YOU)
