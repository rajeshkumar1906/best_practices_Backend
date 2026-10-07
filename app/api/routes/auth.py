from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.dependencies.auth import get_auth_service, get_user_service
from app.schemas.auth import SigninRequest, SignupRequest, TokenResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        return await user_service.create_user(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )


@router.post("/signin", response_model=TokenResponse)
async def signin(
    request: SigninRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    user = await auth_service.authenticate(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return auth_service.create_token(user)