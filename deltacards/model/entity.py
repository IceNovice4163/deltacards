from abc import ABC, ABCMeta
from typing import Any, Iterable, TYPE_CHECKING, Type

from deltacards.actions.methods import ActionProxy
from deltacards.engine.modifiers import IntModifier
from deltacards.model.enums import Ability

if TYPE_CHECKING:
    from deltacards.actions.standard import Action
    from deltacards.actions.results import ActionResult
    from deltacards.engine.game import Game


class EntityMeta(ABCMeta):
    def __new__(mcls, name, bases, attrs):
        attrs['_abilities'] = {}
        attrs['var_definitions'] = {}
        attrs['pre_event_handlers'] = {}
        attrs['post_event_handlers'] = {}

        cls = super().__new__(mcls, name, bases, attrs)

        for ability in Ability:
            effect = getattr(cls, ability.value, None)
            if effect is not None:
                cls._abilities[ability] = effect

        cls._need_condition = getattr(cls, 'need', None)

        return cls


class Entity(ABC, metaclass=EntityMeta):
    __slots__ = 'id', 'state'

    _abilities: dict
    _need_condition: Any | None

    var_definitions: dict
    pre_event_handlers: dict
    post_event_handlers: dict

    def __init__(self, id: int):
        self.id = id

        self.state: dict[str, Any] = {}

    @property
    def actions(self) -> ActionProxy:
        return ActionProxy(self)

    @property
    def base_identity(self) -> tuple[str, int]:
        raise NotImplementedError

    def get_ability(self, ability: Ability):
        effect = self._abilities.get(ability)
        if effect is None:
            return None

        if hasattr(effect, '__get__'):
            return effect.__get__(self, type(self))

        return effect

    def has_ability(self, ability: Ability) -> bool:
        return self._abilities.get(ability) is not None

    def iter_modifiers(self, game: 'Game') -> Iterable[IntModifier]:
        return ()

    def to_snapshot(self):
        raise NotImplementedError

    def serialize(self) -> dict[str, Any]:
        raise NotImplementedError


def on_event(action: Type['Action' | 'ActionResult'], pre: bool = False):
    class OnEvent:
        def __init__(self, function):
            self.function = function

        def __set_name__(self, owner, name):
            event_handlers = owner.pre_event_handlers if pre else owner.post_event_handlers
            event_handlers[action] = self.function

            setattr(owner, name, self.function)

    return OnEvent
