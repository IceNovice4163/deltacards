import inspect
from abc import ABC, ABCMeta
from typing import Any, Iterable, TYPE_CHECKING, Type, get_args

from enums import Ability
from modifiers import IntModifier

if TYPE_CHECKING:
    from actions import Action
    from action_results import ActionResult
    from game import Game


class EntityMeta(ABCMeta):
    def __new__(mcls, name, bases, attrs):
        attrs['_abilities'] = {}
        attrs['var_definitions'] = {}
        attrs['pre_event_handlers'] = {}
        attrs['post_event_handlers'] = {}

        cls = super().__new__(mcls, name, bases, attrs)

        annotations = inspect.get_annotations(cls)
        for attr_name in annotations:
            v = getattr(cls, attr_name, None)
            if hasattr(v, 'eval'):  # check if variable
                args = get_args(annotations[attr_name])
                assert len(args) == 1, "Variable type must be provided"
                v.type = args[0]

                cls.var_definitions[attr_name] = v

        for ability in Ability:
            effect = getattr(cls, ability.value, None)
            if effect is not None:
                cls._abilities[ability] = effect

        return cls


class Entity(ABC, metaclass=EntityMeta):
    __slots__ = 'id'

    _abilities: dict

    var_definitions: dict
    pre_event_handlers: dict
    post_event_handlers: dict

    def __init__(self, id: int):
        self.id = id

    @property
    def base_identity(self) -> tuple[str, int]:
        raise NotImplementedError

    def get_ability(self, ability: Ability):
        effect = self._abilities.get(ability)
        if effect is None:
            return None

        if hasattr(effect, '__get__'):
            return effect.__get__(self, type(self))
        else:
            return effect

    def has_ability(self, ability: Ability):
        return self._abilities.get(ability) is not None

    def iter_modifiers(self, game: 'Game') -> Iterable[IntModifier]:
        return ()

    def serialize(self) -> dict[str, Any]:
        raise NotImplementedError

    turn_start = None
    turn_end = None


def on_event(action: Type['Action' | 'ActionResult'], pre: bool = False):
    class OnEvent:
        def __init__(self, function):
            self.function = function

        def __set_name__(self, owner, name):
            event_handlers = owner.pre_event_handlers if pre else owner.post_event_handlers
            event_handlers[action] = self.function

            setattr(owner, name, self.function)

    return OnEvent
