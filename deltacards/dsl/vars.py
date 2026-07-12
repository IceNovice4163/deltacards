from dataclasses import dataclass
from typing import Any, Generic, TYPE_CHECKING, TypeVar, cast

from deltacards.actions.methods import ActionMethods
from deltacards.dsl.core import (
    TargetSelector,
    ValueExpr,
    resolve_selector_value,
)
from deltacards.engine.effects import StepResult
from deltacards.model.entity import Entity
from deltacards.model.templates import CardTemplate

if TYPE_CHECKING:
    from deltacards.actions.standard import ActionContext


T = TypeVar('T')
_MISSING = object()


class Var(ActionMethods, Generic[T]):
    __slots__ = 'name', 'type', 'default'

    def __new__(cls, type_: type[T], default: Any = _MISSING) -> 'Var[T]':
        if cls is Var:
            try:
                is_selector = (
                    issubclass(type_, TargetSelector)
                    or issubclass(type_, Entity)
                    or issubclass(type_, CardTemplate)
                )
            except TypeError:
                is_selector = False

            var_cls = SelectorVar if is_selector else ValueVar
            return cast('Var[T]', object.__new__(var_cls))

        return cast('Var[T]', object.__new__(cls))

    def __init__(self, type_: type, default: Any = _MISSING):
        self.type = type_
        self.default = default

    def __repr__(self):
        return f'Var({self.type.__name__}, name={self.name}, default={self.default!r})'

    def __set_name__(self, owner, name):
        self.name = name

        if 'var_definitions' not in owner.__dict__:
            owner.var_definitions = dict(owner.var_definitions or {})

        owner.var_definitions[name] = self

    def _get_default_value(self):
        if self.default is not _MISSING:
            return self.default

        return _MISSING

    def _get_value(self, ctx: 'ActionContext') -> Any:
        if self.name is None:
            raise RuntimeError("Var has no name; declare it as a named class attribute")

        try:
            return ctx.vars[self.name]
        except KeyError as exc:
            default = self._get_default_value()
            if default is not _MISSING:
                return default

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

        if issubclass(self.type, StepResult):
            return VarAttrValue(self, name)

        raise AttributeError(name)


class SelectorVar(Var[T], TargetSelector):
    __slots__ = ()

    def _get_default_value(self):
        default = super()._get_default_value()
        if default is _MISSING:
            return []

        return default

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
    var: ValueVar | VarAttrValue
    attr_name: str

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs):
        var = self.var.eval(ctx=ctx, entity=entity, **kwargs)
        return getattr(var, self.attr_name)

    def eval_one(self, ctx: 'ActionContext', **kwargs) -> Any:
        return self.eval(ctx=ctx, **kwargs)

    def eval_optional_one(self, ctx: 'ActionContext', **kwargs) -> Any | None:
        return self.eval(ctx=ctx, **kwargs)

    def __repr__(self) -> str:
        return f"{self.var!r}.{self.attr_name}"

    def __getattr__(self, name: str):
        if name.startswith('__'):
            raise AttributeError(name)

        if name == 'test':  # for evaluate_expr()
            raise AttributeError(name)

        return VarAttrValue(self, name)


class StateVar(Generic[T], ValueExpr):
    __slots__ = 'name', 'owner', 'default'

    def __init__(self, default: Any = _MISSING):
        self.default = default

    def __repr__(self):
        return f'StateVar(name={self.name}, default={self.default!r})'

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

        if 'var_definitions' not in owner.__dict__:
            owner.var_definitions = dict(owner.var_definitions or {})

        owner.var_definitions[name] = self

    def eval(self, ctx: 'ActionContext', entity: Any | None = None, **kwargs) -> Any:
        if self.name is None:
            raise RuntimeError("StateVar has no name; declare it as a named class attribute")

        try:
            return ctx.source.state[self.name]
        except KeyError as exc:
            if self.default is not _MISSING:
                return self.default

            raise RuntimeError(f'StateVar {self.name} is not set on {entity!r}') from exc

    def set_value(self, entity: Any, value: Any):
        entity.state[self.name] = value


VAR = ContextVarSelector
CHOICE_SELECTED = ContextVarSelector('_choice_selected')
CHOICE_NOT_SELECTED = ContextVarSelector('_choice_not_selected')
