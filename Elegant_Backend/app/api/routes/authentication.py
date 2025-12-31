from typing import Optional, Any
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED
from starlette.requests import Request
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta

# --- IMPORTS FROM YOUR APP ---
from app.api.dependencies.database import get_repository
from app.core import config
from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository
from app.models.schemas.users import (
    UserInCreate,
    UserInLogin,
    UserInResponse,
    UserWithToken,
)
from app.models.schemas.AdminSchema import LoginResponse
from app.resources import strings
from app.services import jwt_utils as jwt_service
from app.services.authentication import check_email_is_taken, check_username_is_taken
from app.services.AdminServices import login_user, check_email_exists, reset_password
from app.services.EmailService import EmailService

router = APIRouter()

# --- CONSTANTS ---
ALGORITHM = getattr(config, "ALGORITHM", "HS256")
SECRET_KEY = str(config.SECRET_KEY)

# Define OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/login", response_model=Optional[LoginResponse], name="auth:login")
async def login(
    user_login: UserInLogin = Body(..., embed=True, alias="user"),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    request: Request = None,
) -> LoginResponse:
    wrong_login_error = HTTPException(
        status_code=HTTP_400_BAD_REQUEST, detail=strings.INCORRECT_LOGIN_INPUT
    )
    try:
        user_data = await login_user(request, user_login.email, user_login.password)
        raw = user_data["is_first_login"]
        if user_data:
            token = jwt_service.create_access_token_for_user(user_data, SECRET_KEY)
            return LoginResponse(
                userid=user_data["user_id"],
                username=user_data["user_name"],
                email=user_data["mail_id"],
                roleid=user_data["role_id"],
                token=token,
                is_first_login=raw[0] == 1 if isinstance(raw, (bytes, bytearray)) else raw == 1,   
                 
                )      
        else:
            return None
    except EntityDoesNotExist:
        raise wrong_login_error


@router.post(
    "/register",
    status_code=HTTP_201_CREATED,
    response_model=UserInResponse,
    name="auth:register",
)
async def register(
    user_create: UserInCreate = Body(..., embed=True, alias="user"),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserInResponse:
    if await check_username_is_taken(users_repo, user_create.username):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=strings.USERNAME_TAKEN
        )

    if await check_email_is_taken(users_repo, user_create.email):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=strings.EMAIL_TAKEN
        )
    
    user = await users_repo.create_user(**user_create.dict())
    token = jwt_service.create_access_token_for_user(user, SECRET_KEY)
    
    return UserInResponse(
        user=UserWithToken(
            username=user.username,
            email=user.email,
            bio=user.bio,
            image=user.image,
            token=token,
        )
    )

# --- UPDATED ENDPOINT: GET CURRENT USER PROFILE (/users/me) ---
@router.get("/users/me", response_model=LoginResponse, name="users:me")
async def get_current_user_profile(
    token: str = Depends(oauth2_scheme),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)) 
):
    user_id = None
    email = None

    # STRATEGY 1: Try decoding as a LOCAL token (HS256)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except JWTError:
        # STRATEGY 2: If Local fails, assume it is a MICROSOFT token (RS256)
        try:
            payload = jwt.get_unverified_claims(token)
            email = payload.get("unique_name") or payload.get("upn") or payload.get("email")
        except Exception:
             raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    # DB LOOKUP (Robust Version)
    user_obj = None
    try:
        if user_id:
            # Try normal method
            try:
                user_obj = await users_repo.get_user_by_id(user_id)
            except TypeError:
                # Fallback if arguments are broken
                print("Fallback: Using _log_and_fetch_one for user_id")
                # Using MySQL syntax (%s) as 'DictCursor' implies MySQL
                user_obj = await users_repo._log_and_fetch_one(
                    "SELECT * FROM users_master WHERE user_id = %s", (user_id,)
                )
        elif email:
            # Try normal method
            try:
                user_obj = await users_repo.get_user_by_email(email)
            except TypeError:
                # Fallback if arguments are broken (Takes 1 but 2 given)
                print("Fallback: Using _log_and_fetch_one for email")
                user_obj = await users_repo._log_and_fetch_one(
                    "SELECT * FROM users_master WHERE mail_id = %s", (email,)
                )
        else:
             raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token contains no user identifier")
             
    except Exception as e:
         print(f"DB Error in /users/me: {e}")
         raise HTTPException(status_code=500, detail="Database error retrieving profile")
    
    if not user_obj:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    # MAPPING RESPONSE
    def get_val(obj, key, alt_key=None):
        if isinstance(obj, dict):
            return obj.get(key) or (obj.get(alt_key) if alt_key else None)
        return getattr(obj, key, getattr(obj, alt_key, None) if alt_key else None)

    return LoginResponse(
        userid=get_val(user_obj, "user_id", "id"), 
        username=get_val(user_obj, "user_name", "username"),
        email=get_val(user_obj, "mail_id", "email"),
        roleid=get_val(user_obj, "role_id", "role") or 1,
        token=token 
    )


# --- PASSWORD RESET LOGIC ---

@router.post("/forgotPassword")
async def forgot_password(
    email: str = Body(...),
    org_id: Optional[int] = Body(None),
    request: Request = None
):
    try:
        user = await check_email_exists(email, request)
        if user is None:
            raise HTTPException(status_code=404, detail="Email not found")

        expire = datetime.utcnow() + timedelta(minutes=15)
        token_data = {"user_id": user["user_id"], "exp": expire}
        reset_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        
        email_service = EmailService()
        try:
            await email_service.send_forgot_password_email(
                user_name=user.get("user_name", ""),
                email=email,
                reset_link=reset_link, 
                password=None,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
            return {"message": f"Reset link generated (email failed): {reset_link}"}

        return {"message": "Reset link sent to your email"}

    except HTTPException:
        raise  
    except Exception as e:
        print(f"Forgot password API failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forgot password failed: {e}")

@router.post("/resetPassword")
async def reset_user_password(
    request: Request,
    token: str = Body(...),
    new_password: str = Body(...),
    confirm_password: str = Body(...),
):
    try:
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
        except ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Reset link expired")
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid reset link")

        success = await reset_password(request, user_id, new_password)
        if not success:
            raise HTTPException(status_code=404, detail="User not found or update failed")

        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))