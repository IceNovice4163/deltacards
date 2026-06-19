from dataclasses import dataclass
from typing import Any, Generator, Literal, TYPE_CHECKING

from deltacards.actions.base import Action, ActionContext, bind_ctx_var, evaluate_expr

if TYPE_CHECKING:
    from deltacards.actions.results import ActionResult
    from deltacards.dsl.vars import Var


@dataclass(frozen=True)
class StepResult:
    successes: list[bool]
    results: tuple['ActionResult', ...] = ()

    @property
    def success(self) -> bool:
        return any(self.successes) if self.successes else True

    def __getattr__(self, name: str):  # Used by DSL
        if name.startswith('__'):
            raise AttributeError(name)

        assert len(self.results) == 1
        return getattr(self.results[0], name)


@dataclass(frozen=True)
class EffectResult:
    success: bool


@dataclass(frozen=True)
class EffectStep:
    actions: list[Action]
    kwargs: dict[str, Any]


class EffectBase:
    """
    An Effect is a coroutine-like object which yields EffectStep objects.
    The engine runs the yielded Action list, then resumes this generator by sending StepResult.
    Finally, EffectResult is sent back to the engine.
    """

    def __call__(self, *, ctx: ActionContext, **kwargs) -> Generator[EffectStep, StepResult, EffectResult]:
        raise NotImplementedError

    def __rshift__(self, other: Any) -> 'EffectBase':
        return Seq(effectify(self), effectify(other))

    def __rrshift__(self, other: Any) -> 'EffectBase':
        return Seq(effectify(other), effectify(self))

    def to(self, then: Any, else_: Any | None = None) -> 'EffectBase':
        return Then(effectify(self), effectify(then), effectify(else_) if else_ is not None else None)


def effectify(x: Any) -> EffectBase:
    if isinstance(x, EffectBase):
        return x
    if isinstance(x, Action):
        return Atomic(x)
    if isinstance(x, (list, tuple)):
        return Many([effectify(i) for i in x])
    if callable(x):
        return x

    raise TypeError(f"Failed to convert {x!r} to an effect")


@dataclass(frozen=True)
class Atomic(EffectBase):
    action: Action

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        step_res: StepResult = yield EffectStep([self.action], kwargs=kwargs)
        return EffectResult(success=step_res.success)


@dataclass(frozen=True)
class StoreResult(EffectBase):
    """Wrap an Action and store its outcome in ctx.vars[var.name]."""
    action: Action
    var: 'Var'

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        step_res: StepResult = yield EffectStep([self.action], kwargs=kwargs)
        ctx.vars[self.var.name] = step_res
        return EffectResult(success=step_res.success)


@dataclass(frozen=True)
class Many(EffectBase):
    effects: list[EffectBase | Action]

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        ok = True
        for effect in self.effects:
            res = yield from effect(ctx=ctx, **kwargs)
            if not res.success:
                ok = False

        return EffectResult(success=ok)


@dataclass(frozen=True)
class Seq(EffectBase):
    """A >> B: always run B after A (regardless of A.success)."""
    left: EffectBase | Action
    right: EffectBase | Action

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        left = yield from self.left(ctx=ctx, **kwargs)
        right = yield from self.right(ctx=ctx, **kwargs)

        return EffectResult(success=left.success and right.success)


@dataclass(frozen=True)
class Then(EffectBase):
    """A.to(then): run `then` if A.success is True. Otherwise, run `else` branch if it's defined."""
    cond: EffectBase
    then: EffectBase | Action
    else_: EffectBase | Action | None = None

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        cond = yield from self.cond(ctx=ctx, **kwargs)

        if not cond.success:
            if self.else_ is not None:
                else_ = yield from self.else_(ctx=ctx, **kwargs)
                return EffectResult(success=else_.success)

            return EffectResult(success=False)

        then = yield from self.then(ctx=ctx, **kwargs)
        return EffectResult(success=then.success)


SuccessMode = Literal['all', 'any', 'last']


def _combine_success(successes: list[bool], mode: SuccessMode) -> bool:
    if mode == 'all':
        return all(successes)  # all([]) == True
    if mode == 'any':
        return any(successes)  # any([]) == False
    if mode == 'last':
        return successes[-1] if successes else True

    raise ValueError(f"Invalid mode: {mode}")


@dataclass(frozen=True)
class Check(EffectBase):
    cond: Any

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        ok = bool(evaluate_expr(self.cond, ctx=ctx, **kwargs))
        yield from ()  # make this function a generator
        return EffectResult(success=ok)


@dataclass(frozen=True)
class For(EffectBase):
    count: Any
    effect: EffectBase | Action
    index_var: 'Var | None' = None
    success_mode: SuccessMode = 'any'

    def __post_init__(self):
        object.__setattr__(self, 'effect', effectify(self.effect))

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        count = evaluate_expr(self.count, ctx=ctx, **kwargs)
        if count < 0:
            raise ValueError(f"For(count) must be >= 0, got {count}")

        successes: list[bool] = []
        for i in range(count):
            if self.index_var is not None:
                with bind_ctx_var(ctx, self.index_var.name, i):
                    res = yield from self.effect(ctx=ctx, **kwargs)
            else:
                res = yield from self.effect(ctx=ctx, **kwargs)

            successes.append(bool(res.success))

        return EffectResult(success=_combine_success(successes, self.success_mode))


@dataclass(frozen=True)
class ForEach(EffectBase):
    iterable: Any
    effect: EffectBase | Action
    var: 'Var'
    index_var: 'Var | None' = None
    success_mode: SuccessMode = 'any'

    def __post_init__(self):
        object.__setattr__(self, 'effect', effectify(self.effect))

    def __call__(
        self, *, ctx: ActionContext, **kwargs
    ) -> Generator[EffectStep, StepResult, EffectResult]:
        raw_items = evaluate_expr(self.iterable, ctx=ctx, **kwargs)
        item_exprs = list(raw_items)

        successes: list[bool] = []
        for index, item in enumerate(item_exprs):
            if self.index_var is not None:
                with bind_ctx_var(ctx, self.index_var.name, index), bind_ctx_var(ctx, self.var.name, item):
                    res = yield from self.effect(ctx=ctx, **kwargs)
            else:
                with bind_ctx_var(ctx, self.var.name, item):
                    res = yield from self.effect(ctx=ctx, **kwargs)

            successes.append(bool(res.success))

        return EffectResult(success=_combine_success(successes, self.success_mode))
