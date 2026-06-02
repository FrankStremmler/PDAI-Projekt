from abc import ABC, abstractmethod


class ProviderBase(ABC):
    """Basis-Klasse für einen Anbieter-Wrap.

    Später können Google- und Microsoft-spezifische Adapter hiervon erben.
    """

    @abstractmethod
    def authenticate(self):
        raise NotImplementedError

    @abstractmethod
    def list_items(self):
        raise NotImplementedError

    @abstractmethod
    def sync(self):
        raise NotImplementedError
