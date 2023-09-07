from abc import ABC, abstractmethod


class Entity(ABC):
    __slots__ = ()

    @abstractmethod
    def copy(self, **kwargs):
        pass
