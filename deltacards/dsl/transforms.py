from dataclasses import dataclass
from typing import Any, Literal, TYPE_CHECKING

from deltacards.dsl.core import TargetSelector, TargetingError, Transform, ValueExpr
from deltacards.dsl.selectors import YOU
from deltacards.dsl.values import TEMPLATE_ID
from deltacards.model.cards import Card, CardZone, Monster
from deltacards.model.entity import Entity
from deltacards.model.player import Player
from deltacards.model.templates import CardTemplate

if TYPE_CHECKING:
    from deltacards.actions.standard import ActionContext


@dataclass(frozen=True, slots=True, eq=False)
class RandomTransform(Transform):
    """Get `n` random entities from a list"""
    n: int = 1

    def apply(self, entities: list[Any], ctx: 'ActionContext', **kwargs) -> list[Any]:
        if self.n <= 0 or not entities:
            return []

        items = entities.copy()
        ctx.game.rng.shuffle(items)

        return items[:self.n]

    def __repr__(self) -> str:
        return f"RANDOM({self.n})"


@dataclass(frozen=True, slots=True, eq=False)
class MinMaxTransform(Transform):
    mode: Literal['min', 'max']
    key: ValueExpr
    n: int = 1

    def apply(self, entities: list[Any], ctx: 'ActionContext', **kwargs) -> list[Any]:
        if self.n <= 0 or not entities:
            return []

        sorted_entities = sorted(
            entities,
            key=lambda e: self.key.eval(ctx=ctx, entity=e, **kwargs),
            reverse=(self.mode == 'max'),
        )
        return sorted_entities[:self.n]

    def __repr__(self) -> str:
        name = "MAX" if self.mode == 'max' else "MIN"
        return f"{name}({self.key!r}, n={self.n})"


@dataclass(frozen=True, slots=True, eq=False)
class LeftRightMostTransform(Transform):
    mode: Literal['left', 'right']

    def apply(self, entities: list[Any], ctx: 'ActionContext', **kwargs) -> list[Any]:
        if not entities:
            return []

        for e in entities:
            if (not isinstance(e, Monster)) or (e.zone is not CardZone.BOARD):
                raise TargetingError(f"{self.mode.upper()}MOST expects monsters on board")

        reverse = (self.mode == 'right')
        return [sorted(entities, key=lambda m: m.pos, reverse=reverse)[0]]

    def __repr__(self) -> str:
        return "RIGHTMOST" if self.mode == 'right' else "LEFTMOST"


LEFTMOST = LeftRightMostTransform('left')
RIGHTMOST = LeftRightMostTransform('right')


@dataclass(frozen=True, slots=True, eq=False)
class DistinctTransform(Transform):
    key: ValueExpr

    def apply(self, entities: list[Any], ctx: 'ActionContext', **kwargs) -> list[Any]:
        result = []
        seen = set()

        for entity in entities:
            key = self.key.eval(ctx=ctx, entity=entity, **kwargs)
            if key in seen:
                continue

            seen.add(key)
            result.append(entity)

        return result

    def __repr__(self) -> str:
        return f"DISTINCT({self.key!r})"


@dataclass(frozen=True, slots=True, eq=False)
class SortByTransform(Transform):
    key: ValueExpr
    reverse: bool = False

    def apply(self, entities: list[Any], ctx: 'ActionContext', **kwargs) -> list[Any]:
        return sorted(
            entities,
            key=lambda entity: self.key.eval(ctx=ctx, entity=entity, **kwargs),
            reverse=bool(self.reverse),
        )

    def __repr__(self) -> str:
        return f"SORT_BY({self.key!r}, reverse={self.reverse})"


@dataclass(frozen=True, slots=True, eq=False)
class GenerateCardsTransform(Transform):
    controller: TargetSelector
    creator: TargetSelector | None

    def apply(self, entities: list[Any], ctx: 'ActionContext', **kwargs) -> list[Any]:
        controller = self.controller.eval_optional_one(ctx=ctx, **kwargs)
        if controller is None:
            return []

        if not isinstance(controller, Player):
            raise TargetingError(f"GENERATE() controller must be a player, got {type(controller).__name__}")

        creator_id = None
        creator_base_identity = None

        if self.creator is not None:
            creator = self.creator.eval_optional_one(ctx=ctx, **kwargs)
            if creator is not None:
                creator_base_identity = creator.base_identity
                if isinstance(creator, Entity):
                    creator_id = creator.id

        assert all(isinstance(e, CardTemplate) for e in entities)
        template_ids = tuple(template.id for template in entities)

        result = []
        for template_id in template_ids:
            result.append(
                ctx.game.create_card(
                    template_id=template_id,
                    controller_id=controller.id,
                    creator_id=creator_id,
                    creator_base_identity=creator_base_identity,
                )
            )

        return result

    def __repr__(self) -> str:
        return f"GENERATE(controller={self.controller!r}, creator={self.creator!r})"


@dataclass(frozen=True, slots=True, eq=False)
class CopyTransform(Transform):
    exact: bool
    controller: TargetSelector
    creator: TargetSelector | None = None

    def _resolve_creator(self, ctx: 'ActionContext', **kwargs) -> Entity | None:
        if self.creator is None:
            if isinstance(ctx.source, Entity):
                return ctx.source
            else:
                raise TargetingError(f"COPY(): unable to identify copy source from `ctx.source`")

        creator = self.creator.eval_optional_one(ctx=ctx, **kwargs)
        if creator is None:
            raise TargetingError(f"COPY(): unable to identify copy source from `creator`")

        if not isinstance(creator, Entity):
            raise TargetingError(f"COPY() creator must be an entity, got {type(creator).__name__}")

        return creator

    def apply(self, entities: list[Any], ctx: 'ActionContext', **kwargs) -> list[Any]:
        if not entities:
            return []

        controller = self.controller.eval_optional_one(ctx=ctx, **kwargs)
        if controller is None:
            return []

        creator = self._resolve_creator(ctx, **kwargs)

        assert all(isinstance(e, Card) for e in entities)

        result = []
        for card in entities:
            if self.exact:
                result.append(
                    ctx.game.create_card_copy_exact(
                        card,
                        controller_id=controller.id,
                        creator_id=creator.id,
                        creator_base_identity=creator.base_identity,
                    )
                )
            else:
                result.append(
                    ctx.game.create_card_copy(
                        card,
                        controller_id=controller.id,
                        creator_id=creator.id,
                        creator_base_identity=creator.base_identity,
                    )
                )

        return result

    def __repr__(self) -> str:
        name = "EXACT_COPY" if self.exact else "COPY"
        args = []

        if self.controller is not YOU:
            args.append(f"controller={self.controller!r}")
        if self.creator is not None:
            args.append(f"creator={self.creator!r}")

        return f"{name}({', '.join(args)})"


def RANDOM(n: int = 1) -> RandomTransform:
    return RandomTransform(n)


def MIN(key: ValueExpr, n: int = 1) -> MinMaxTransform:
    return MinMaxTransform('min', key=key, n=n)


def MAX(key: ValueExpr, n: int = 1) -> MinMaxTransform:
    return MinMaxTransform('max', key=key, n=n)


def DISTINCT(key: ValueExpr | None = None) -> DistinctTransform:
    return DistinctTransform(key=TEMPLATE_ID if key is None else key)


def SORT_BY(key: ValueExpr, reverse: bool = False) -> SortByTransform:
    return SortByTransform(key=key, reverse=reverse)


def GENERATE(
    controller: TargetSelector | None = None,
    creator: TargetSelector | None = None,
) -> GenerateCardsTransform:
    return GenerateCardsTransform(
        controller=YOU if controller is None else controller,
        creator=creator,
    )


def COPY(
    controller: TargetSelector | None = None,
    creator: TargetSelector | None = None,
) -> CopyTransform:
    return CopyTransform(
        exact=False,
        controller=YOU if controller is None else controller,
        creator=creator,
    )


def EXACT_COPY(
    controller: TargetSelector | None = None,
    creator: TargetSelector | None = None,
) -> CopyTransform:
    return CopyTransform(
        exact=True,
        controller=YOU if controller is None else controller,
        creator=creator,
    )
