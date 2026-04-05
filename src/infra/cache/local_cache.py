from typing import Any, Set, Dict, List, Optional
from ..template.cache import ICache
from ..util.time_util import current_seconds
import logging

log = logging.getLogger(__name__)


class LocalCache(ICache):
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.ttl: Dict[str, int] = {}

    # default with_ttl is True, make 'TTL' works
    async def get(self, key: str, with_ttl: bool = True):
        if with_ttl and key in self.cache:
            now = current_seconds()
            if key in self.ttl and self.ttl[key] < now:
                await self.delete(key)
                return None
            else:
                return self.cache[key]

        if key in self.cache:
            return self.cache[key]
        return None

    async def set(self, key: str, val: Any, ex: int = None):
        if key is None:
            log.error('local cache key is None key: %s, val: %s, ex: %s', key, val, ex)
            return

        self.cache[key] = val
        if ex is not None:
            now = current_seconds()
            self.ttl[key] = now + ex

    async def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
            del self.ttl[key]

    async def smembers(self, key: str) -> (Optional[Set[Any]]):
        return

    async def sismember(self, key: str, value: Any) -> (bool):
        return False

    async def sadd(self, key: str, values: List[Any], ex: int = None) -> (int):
        return 0

    async def srem(self, key: str, value: Any) -> (int):
        return 0

_local_cache = LocalCache()
