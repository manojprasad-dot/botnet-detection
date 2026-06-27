from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user import User
from database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()


user_repository = UserRepository(User)
