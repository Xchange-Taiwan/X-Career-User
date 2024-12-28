'''
interface Repository<
  Id extends EntityId<unknown>,
  A extends AggregateRoot<Id, {}>
> {
  exists(id: Id): Promise<boolean>;
  findById(id: Id): Promise<A | undefined>;
  // 提供更靈活的搜尋條件
  findAllMatching(querystring: string): Promise<A[]>;
  add(entity: Entity): Promise<void>;
  update(entity: A): Promise<void>;
  remove(id: Id): Promise<void>;
}
'''
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List

class IRepository(ABC):
    @abstractmethod
    def exists(self, id: int) -> bool:
        pass

    @abstractmethod
    def find_by_id(self, id: int) -> Optional[TypeVar('A')]:
        pass

    @abstractmethod
    def find_all_matching(self, querystring: str) -> List[TypeVar('A')]:
        pass

    @abstractmethod
    def add(self, entity: TypeVar('A')) -> None:
        pass

    @abstractmethod
    def update(self, entity: TypeVar('A')) -> None:
        pass

    @abstractmethod
    def remove(self, id: int) -> None:
        pass