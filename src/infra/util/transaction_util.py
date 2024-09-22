from typing import Callable, Any, Awaitable, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps

T = TypeVar('T', bound=Callable[..., Any])


# Type hint for async session
def async_transactional(session_factory: Callable[[], AsyncSession]) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with session_factory() as session:
                try:
                    result = await func(session=session, *args, **kwargs)  # Pass session to the function
                    await session.commit()  # Commit if successful
                    return result
                except SQLAlchemyError as e:
                    await session.rollback()  # Rollback in case of error
                    print(f"Transaction rolled back due to: {e}")
                    raise

        return wrapper

    return decorator


# Type hint for sync session
def transactional(session_factory: Callable[[], Session]) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            session = session_factory()
            try:
                result = func(*args, session=session, **kwargs)
                session.commit()
                return result
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Transaction rolled back due to: {e}")
                raise
            finally:
                session.close()

        return wrapper

    return decorator
