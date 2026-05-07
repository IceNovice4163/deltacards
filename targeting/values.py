from dataclasses import dataclass
from typing import Any, Literal, TYPE_CHECKING

from cards import Card, CardZone
from cards.templates import CardTemplate
from player import Player

from .core import TargetSelector, TargetingError, ValueExpr, to_value

if TYPE_CHECKING:
    from actions import ActionContext


@dataclass(frozen=True, slots=True, eq=False)
class AttrValue(ValueExpr):
    """
    Get attribute of the candidate entity.
    Example: COST
    """
    attr: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        if entity is None:
            raise TargetingError(f"{self.attr.upper()} requires a candidate entity")

        try:
            return getattr(entity, self.attr)
        except AttributeError as e:
            raise TargetingError(f"{self.attr.upper()} attribute is not available on {type(entity).__name__}") from e

    def __repr__(self) -> str:
        return self.attr.upper()


@dataclass(frozen=True, slots=True, eq=False)
class TemplateIdValue(ValueExpr):
    """
    Get template id of the candidate entity.
    Example: TEMPLATE_ID
    """

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> int:
        if entity is None:
            raise TargetingError("TEMPLATE_ID requires a candidate entity")

        if isinstance(entity, CardTemplate):
            return entity.id

        if isinstance(entity, Card):
            return entity.template.id

        raise TargetingError(f"TEMPLATE_ID is not available on {type(entity).__name__}")

    def __repr__(self) -> str:
        return "TEMPLATE_ID"


@dataclass(frozen=True, slots=True, eq=False)
class BaseStatValue(ValueExpr):
    """
    Get base stat of the candidate entity.
    Example: BASE_COST
    """
    attr: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        if entity is None:
            raise TargetingError(f"BASE_{self.attr.upper()} requires a candidate entity")

        if isinstance(entity, Card):
            try:
                return getattr(entity.base, self.attr)
            except AttributeError as e:
                raise TargetingError(f"Card.base.{self.attr} is missing on {entity!r} (wrong card type?)") from e

        if isinstance(entity, CardTemplate):
            try:
                return getattr(entity, self.attr)
            except AttributeError as e:
                raise TargetingError(f"CardTemplate.{self.attr} is missing on {entity!r} (wrong card type?)") from e

        raise TargetingError(f"BASE_{self.attr.upper()} is not available on {type(entity).__name__}")

    def __repr__(self) -> str:
        return f"BASE_{self.attr.upper()}"


@dataclass(frozen=True, slots=True, eq=False)
class SelectorAttrValue(ValueExpr):
    """
    Get attribute of the entity resolved by selector.
    Example: TARGET.cost
    """
    selector: TargetSelector
    attr: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        target = self.selector.eval_one(ctx=ctx, **kwargs)

        if self.attr == 'controller':
            return ctx.game.player(target.controller_id)

        try:
            return getattr(target, self.attr)
        except AttributeError as e:
            raise TargetingError(f"{self.selector!r}.{self.attr} is not available on {type(target).__name__}") from e

    def __repr__(self) -> str:
        return f"{self.selector!r}.{self.attr}"


@dataclass(frozen=True, slots=True, eq=False)
class SelectorBaseStatValue(ValueExpr):
    """
    Get base stat of the entity resolved by selector.
    Example: TARGET.base.cost
    """
    selector: TargetSelector
    attr: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        target = self.selector.eval_one(ctx=ctx, **kwargs)

        try:
            return getattr(target.base, self.attr)
        except AttributeError as e:
            raise TargetingError(f"{self.selector!r}.base.{self.attr} is not available on {type(target).__name__}") from e

    def __repr__(self) -> str:
        return f"{self.selector!r}.base.{self.attr}"


@dataclass(frozen=True, slots=True, eq=False)
class SelectorBuffValue(ValueExpr):
    """
    Get stat buff value of the entity resolved by selector.
    Example: TARGET.buffs.cost
    """
    selector: TargetSelector
    attr: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        target = self.selector.eval_one(ctx=ctx, **kwargs)

        try:
            return getattr(target.buffs, self.attr)
        except AttributeError as e:
            raise TargetingError(f"{self.selector!r}.buffs.{self.attr} is not available on {type(target).__name__}") from e

    def __repr__(self) -> str:
        return f"{self.selector!r}.buffs.{self.attr}"


@dataclass(frozen=True, slots=True, eq=False)
class CountValue(ValueExpr):
    selector: TargetSelector

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> int:
        return len(self.selector.eval(ctx=ctx, **kwargs))

    def __repr__(self) -> str:
        return f"COUNT({self.selector!r})"


def COUNT(selector: TargetSelector) -> CountValue:
    return CountValue(selector)


@dataclass(frozen=True, slots=True, eq=False)
class ClampValue(ValueExpr):
    value: ValueExpr
    lower: ValueExpr
    upper: ValueExpr

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        value = self.value.eval(ctx=ctx, entity=entity, **kwargs)
        lower = self.lower.eval(ctx=ctx, entity=entity, **kwargs)
        upper = self.upper.eval(ctx=ctx, entity=entity, **kwargs)

        assert lower <= upper
        return max(lower, min(value, upper))

    def __repr__(self) -> str:
        return f"CLAMP({self.value!r}, {self.lower!r}, {self.upper!r})"


def CLAMP(value: Any, lower: Any, upper: Any) -> ClampValue:
    return ClampValue(to_value(value), to_value(lower), to_value(upper))


@dataclass(frozen=True, slots=True, eq=False)
class LeastGreatestValue(ValueExpr):
    mode: Literal['least', 'greatest']
    a: ValueExpr
    b: ValueExpr

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        a = self.a.eval(ctx=ctx, entity=entity, **kwargs)
        b = self.b.eval(ctx=ctx, entity=entity, **kwargs)

        if self.mode == 'least':
            return a if a <= b else b
        else:
            return a if a >= b else b

    def __repr__(self) -> str:
        name = "LEAST" if self.mode == 'least' else "GREATEST"
        return f"{name}({self.a!r}, {self.b!r})"


def LEAST(a: Any, b: Any) -> LeastGreatestValue:
    return LeastGreatestValue('least', to_value(a), to_value(b))


def GREATEST(a: Any, b: Any) -> LeastGreatestValue:
    return LeastGreatestValue('greatest', to_value(a), to_value(b))


@dataclass(frozen=True, slots=True, eq=False)
class EmptySlotsValue(ValueExpr):
    selector: TargetSelector

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> int:
        from .selectors import ZoneSelector

        if not isinstance(self.selector, ZoneSelector):
            raise TargetingError(f"EMPTY_SLOTS expects a ZoneSelector, got {self.selector!r}")

        used = len(self.selector.eval(ctx=ctx, **kwargs))

        player = self.selector.player.eval_one(ctx=ctx, **kwargs)
        if self.selector.zone == CardZone.BOARD:
            cap = int(player.board.MAX_CARDS)
        elif self.selector.zone == CardZone.HAND:
            cap = 7
        else:
            raise TargetingError(f"EMPTY_SLOTS only supports HAND/BOARD, got {self.selector.zone}")

        return max(cap - used, 0)

    def __repr__(self) -> str:
        return f"EMPTY_SLOTS({self.selector!r})"


def EMPTY_SLOTS(selector: TargetSelector) -> EmptySlotsValue:
    return EmptySlotsValue(selector=selector)


@dataclass(frozen=True, slots=True, eq=False)
class SynergyTriggeredValue(ValueExpr):
    """
    Can only be used inside MAGIC trigger of a monster.
    Returns True if SYNERGY was triggered.
    """
    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> bool:
        return ctx.env.get('synergy_triggered', False)

    def __repr__(self) -> str:
        return "SYNERGY_TRIGGERED"


@dataclass(frozen=True, slots=True, eq=False)
class HasArtifactValue(ValueExpr):
    artifact_name: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> bool:
        if entity is None:
            raise TargetingError(f"HAS_ARTIFACT requires a candidate entity")

        if not isinstance(entity, Player):
            raise TargetingError(f"HAS_ARTIFACT is not available on {type(entity).__name__}")

        return any(artifact.name == self.artifact_name for artifact in entity.artifacts)

    def __repr__(self) -> str:
        return "HAS_ARTIFACT"


ID = AttrValue('id')

TEMPLATE_ID = TemplateIdValue()

COST = AttrValue('cost')
RARITY = AttrValue('rarity')

ATTACK = AttrValue('attack')
HP = AttrValue('hp')
MAX_HP = AttrValue('max_hp')
CREATOR_ID = AttrValue('creator_id')

BASE_COST = BaseStatValue('cost')
BASE_ATTACK = BaseStatValue('attack')
BASE_HP = BaseStatValue('hp')

SYNERGY_TRIGGERED = SynergyTriggeredValue()

HAS_ARTIFACT = HasArtifactValue
