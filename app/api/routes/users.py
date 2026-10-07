from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user, get_user_service
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        
        updated_user = await user_service.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )