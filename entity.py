from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from actions import Action


class EntityMeta(ABCMeta):
    def __new__(cls, name, bases, attrs):
        attrs['pre_event_handlers'] = {}
        attrs['post_event_handlers'] = {}

        return super().__new__(cls, name, bases, attrs)


class Entity(ABC, metaclass=EntityMeta):
    __slots__ = ()

    pre_event_handlers: dict
    post_event_handlers: dict

    @abstractmethod
    def copy(self, **kwargs):
        pass


def on_event(action: Type['Action'], pre: bool = False):
    class OnEvent:
        def __init__(self, function):
            self.function = function

        def __set_name__(self, owner, name):
            event_handlers = owner.pre_event_handlers if pre else owner.post_event_handlers
            event_handlers[action] = self.function

            setattr(owner, name, self.function)

    return OnEvent
