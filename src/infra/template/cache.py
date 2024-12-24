from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Optional


class ICache(ABC):

    @abstractmethod
    async def get(self, key: str, with_ttl: bool = False):
        pass

    @abstractmethod
    async def set(self, key: str, val: Any, ex: int = None):
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

    @abstractmethod
    async def smembers(self, key: str) -> (Optional[Set[Any]]):
        pass

    @abstractmethod
    async def sismember(self, key: str, value: Any) -> (bool):
        pass

    @abstractmethod
    async def sadd(self, key: str, values: List[Any], ex: int = None) -> (int):
        pass

    @abstractmethod
    async def srem(self, key: str, value: Any) -> (int):
        pass
