from fastapi import APIRouter, Body, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from starlette.requests import Request

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
# from app.services import jwt
from app.services import jwt as jwt_service
from app.services.authentication import check_email_is_taken, check_username_is_taken
from app.services.AdminServices import login_user,check_email_exists, reset_password

# Correct: import the class, not the module
from app.services.EmailService import EmailService

from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from starlette.requests import Request
from app.services import UserService 
from app.models.schemas.AdminSchema import LoginResponse




from typing import Optional

router = APIRouter()


@router.post("/login", response_model=Optional[LoginResponse], name="auth:login")
async def login(
    # request1: LoginResponse,
    user_login: UserInLogin = Body(..., embed=True, alias="user"),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    request: Request = None,
) -> LoginResponse:
    wrong_login_error = HTTPException(
        status_code=HTTP_400_BAD_REQUEST, detail=strings.INCORRECT_LOGIN_INPUT
    )
    try:
        
        #updateTermConditionFlag = await UserService.update_term_condition_flag(request1.userid, request1.roleid, request1.orgid, request)
        
        # First try to get user from users_master table (for role-based auth)
        user_data = await login_user(request, user_login.email, user_login.password)
        
        if user_data:
            token = jwt_service.create_access_token_for_user(user_data, str(config.SECRET_KEY))
            
            # Return LoginResponse with all the fields you specified
            return LoginResponse(
                userid=user_data["user_id"],
                username=user_data["user_name"],
                email=user_data["mail_id"],
                orgid=user_data["org_id"],
                orgname=user_data["org_name"],
                roleid=user_data["role_id"],
                rolename=user_data["role_name"],
                provider=user_data.get("provider"),   
                token=token,
                term_condition_flag=user_data.get("term_condition_flag", 0)  # ✅ include flag
            )
        
        else:
            return None
    except EntityDoesNotExist:
        raise wrong_login_error
    


@router.post(
    "",
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

    token = jwt_service.create_access_token_for_user(user, str(config.SECRET_KEY))
    return UserInResponse(
        user=UserWithToken(
            username=user.username,
            email=user.email,
            bio=user.bio,
            image=user.image,
            token=token,
        )
    )


SECRET_KEY = "your_super_secret_key"  # use env variable
ALGORITHM = "HS256"

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

        # Generate short-lived token (15 min)
        expire = datetime.utcnow() + timedelta(minutes=15)
        token_data = {"user_id": user["user_id"], "exp": expire}
        reset_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        #Create reset link (frontend route)
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        #reset_link = f"https://icaptureapp.com/reset-password?token={reset_token}"
        # Send via email
        email_service = EmailService()
        try:
            await email_service.send_forgot_password_email(
                user_name=user.get("user_name", ""),
                email=email,
                reset_link=reset_link, 
                password=None,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")  # logging
            # Optional: still return success for testing
            return {"message": f"Reset link generated (email failed): {reset_link}"}

        return {"message": "Reset link sent to your email"}

    except HTTPException:
        raise  # re-raise known HTTP exceptions
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

        #Decode token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            #org_id = payload.get("org_id")
        except ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Reset link expired")
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid reset link")

        # Update password
        success = await reset_password(request, user_id,new_password)
        if not success:
            raise HTTPException(status_code=404, detail="User not found or update failed")

        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# #Forgot Password End Point
# @router.post("/forgotPassword")
# async def forgot_password(
#     email: str = Body(...),
#     org_id: int = Body(...),
#     request: Request = None
# ):
#     try:
#         user = await check_email_exists(email, org_id, request)
#         if user is None:
#             raise HTTPException(status_code=404, detail="Email not found")
#         return {
#             "message": "Email verified. Proceed to reset password.",
#             "user_id": user["user_id"]  # access as dict
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# #Password Reset
# @router.post("/resetPassword")
# async def reset_user_password(
#     request: Request,
#     user_id: int = Body(...),
#     org_id: int = Body(...),
#     new_password: str = Body(...),
#     confirm_password: str = Body(...),
# ):
#     try:
#         # user = await check_email_exists_by_id(user_id, org_id, request)
#         # if user is None:
#         #     raise HTTPException(status_code=404, detail="User not found")
#         if new_password != confirm_password:
#             raise HTTPException(status_code=400, detail="Passwords do not match")
        
#         success = await reset_password(request, user_id, org_id, new_password)
#         if success is False:
#             raise HTTPException(status_code=404, detail="User not found or update failed")
#         else:
#             return {"message": "Password updated successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))