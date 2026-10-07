from typing import Optional

from app.core.security import get_password_hash
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        normalized_email = user_data.email.lower()

        if await self.user_repo.exists_by_email(normalized_email):
            raise ValueError("User already exists")

        password_hash = get_password_hash(user_data.password)

        user = User(
            name=user_data.name,
            email=normalized_email,
            password_hash=password_hash,
        )

        created_user = await self.user_repo.create(user)
        return UserResponse.model_validate(created_user)

    async def get_current_user(self, user_id: int) -> Optional[UserResponse]:
        user = await self.user_repo.get_by_id(user_id)
        if user:
            return UserResponse.model_validate(user)
        return None

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        if user_data.name is not None:
            user.name = user_data.name
        if user_data.email is not None:
            if await self.user_repo.exists_by_email(user_data.email.lower()):
                raise ValueError("Email already in use")
            user.email = user_data.email.lower()

        updated_user = await self.user_repo.update(user)
        return UserResponse.model_validate(updated_user)