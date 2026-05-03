from dataclasses import dataclass
from typing import Any, Generic, TYPE_CHECKING, TypeVar

from entity import Entity

from .core import TargetSelector, ValueExpr, resolve_selector_value

if TYPE_CHECKING:
    from actions import ActionContext


T = TypeVar('T')
_MISSING = object()


class Var(Generic[T]):
    __slots__ = 'name', 'type', 'default'

    def __new__(cls, type_: type, default: Any = _MISSING) -> 'Var':
        if cls is Var:
            try:
                is_selector = issubclass(type_, TargetSelector)
            except TypeError:
                is_selector = False

            var_cls = SelectorVar if is_selector else ValueVar
            return super().__new__(var_cls)

        return super().__new__(cls)

    def __init__(self, type_: type, default: Any = _MISSING):
        self.type = type_
        self.default = default

    def __repr__(self):
        return f'Var({self.type}, name={self.name})'

    def __set_name__(self, owner, name):
        self.name = name

    def _get_value(self, ctx: 'ActionContext') -> Any:
        if self.name is None:
            raise RuntimeError("Var has no name; declare it as a named class attribute")

        try:
            return ctx.vars[self.name]
        except KeyError as exc:
            if self.default is not _MISSING:
                return self.default

            raise RuntimeError(f'Var {self.name} is not set in the current effect scope') from exc


class ValueVar(Var[T], ValueExpr):
    __slots__ = ()

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        value = self._get_value(ctx)

        if isinstance(value, ValueExpr):
            return value.eval(ctx=ctx, entity=entity, **kwargs)

        return value

    def __getattr__(self, name: str):
        if name.startswith('__'):
            raise AttributeError(name)

        if issubclass(self.type, Entity):
            return VarAttrValue(self, name)

        from effects import StepResult
        if issubclass(self.type, StepResult):
            return VarAttrValue(self, name)

        raise AttributeError(name)


class SelectorVar(Var[T], TargetSelector):
    __slots__ = ()

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        value = self._get_value(ctx)
        return resolve_selector_value(value, ctx=ctx, **kwargs)


@dataclass(frozen=True, slots=True, eq=False)
class ContextVarSelector(TargetSelector):
    name: str

    def eval(self, ctx: 'ActionContext', **kwargs) -> list[Any]:
        return resolve_selector_value(ctx.vars.get(self.name), ctx=ctx, **kwargs)

    def __repr__(self) -> str:
        return f"VAR({self.name})"


@dataclass(frozen=True, slots=True, eq=False)
class VarAttrValue(ValueExpr):
    var: ValueVar
    attr_name: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs):
        step_res = self.var.eval(ctx=ctx, entity=entity, **kwargs)
        return getattr(step_res, self.attr_name)

    def eval_one(self, ctx: 'ActionContext', **kwargs) -> Any:
        return self.eval(ctx=ctx, **kwargs)

    def eval_optional_one(self, ctx: 'ActionContext', **kwargs) -> Any | None:
        return self.eval(ctx=ctx, **kwargs)

    def __repr__(self) -> str:
        return f"{self.var!r}.{self.attr_name}"


VAR = ContextVarSelector
CHOICE_SELECTED = ContextVarSelector('_choice_selected')
CHOICE_NOT_SELECTED = ContextVarSelector('_choice_not_selected')
