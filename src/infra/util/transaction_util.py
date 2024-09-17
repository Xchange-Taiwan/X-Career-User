from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

def async_transactional(session_factory):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with session_factory() as session:
                try:
                    result = await func(*args, session=session, **kwargs)  # Pass session to the function
                    await session.commit()  # Commit if successful
                    return result
                except SQLAlchemyError as e:
                    await session.rollback()  # Rollback in case of error
                    print(f"Transaction rolled back due to: {e}")
                    raise
        return wrapper
    return decorator

def transactional(session_factory):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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