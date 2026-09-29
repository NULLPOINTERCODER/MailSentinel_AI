from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_user_service
from app.core.security import create_access_token
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.user_service import UserService, user_doc_to_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """Register a new user account and return an access token."""
    existing_user = await user_service.get_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    user_doc = await user_service.create_user(payload)
    token = create_access_token(subject=str(user_doc["_id"]))

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_doc_to_response(user_doc),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """Authenticate with email and password and return an access token."""
    user_doc = await user_service.authenticate(payload.email, payload.password)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    token = create_access_token(subject=str(user_doc["_id"]))

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_doc_to_response(user_doc),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Fetch profile details of the currently authenticated user."""
    return current_user
