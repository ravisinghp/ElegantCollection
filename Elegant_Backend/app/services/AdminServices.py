from starlette.requests import Request
from fastapi import HTTPException
from app.models.schemas.AdminSchema import (
    UserCreate,
    UserUpdate,
    KeywordCreate,
    RoleResponse,
    CategoryResponse,
    EmailSettings,
    KeywordUpdate,
)
from starlette.status import HTTP_400_BAD_REQUEST
from app.models.domain.AdminDomain import UserInDB, KeywordMaster
from app.db.repositories import AdminRepo as admin_repo
from app.db.repositories import AdminRepo
from typing import List, Dict, Any
from collections import Counter
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from app.db.repositories import AdminRepo 
from app.db.repositories.AdminRepo import get_user_by_email_id,update_user_password

from app.services.EmailService import EmailService

email_settings = EmailSettings()

# create the mail config (conf)
conf = ConnectionConfig(
    MAIL_USERNAME=email_settings.MAIL_USERNAME,
    MAIL_PASSWORD=email_settings.MAIL_PASSWORD,
    MAIL_FROM=email_settings.MAIL_FROM,
    MAIL_FROM_NAME=email_settings.MAIL_FROM_NAME,
    MAIL_PORT=email_settings.MAIL_PORT,
    MAIL_SERVER=email_settings.MAIL_SERVER,
    MAIL_STARTTLS=email_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=email_settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=email_settings.USE_CREDENTIALS,
)
# from app.db.repositories.AdminRepo import get_users, get_users_count



# register User
async def register_user(request: Request, user: UserCreate) -> int:
    # Check if user exists by email
    existing_user = await admin_repo.get_user_by_email(request, user.mail_id,user.org_id)
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User already exists with this email"
        )

    role_id = user.role_id
    org_id = user.org_id

    # Hash password
    hashed_password = admin_repo.hash_password(user.password)

    # Create UserInDB dict and instance
    user_dict = user.dict()
    user_dict.update({"password": hashed_password})

    # for fetching the data
    user_in_db = UserInDB(
        user_id=0,  # DB should generate this
        user_name=user.user_name,
        mail_id=user.mail_id,
        password=hashed_password,
        org_id=org_id,
        role_id=role_id,
        folder_name=user.folder_name,
        created_by=user.created_by,
        provider=user.provider,
    )

    # Save user
    user_id = await admin_repo.create_user(
        request, user_in_db, org_id, role_id, user.created_by
    )

    #   send mail to the created user
    # message = MessageSchema(
    #     subject="Welcome to Our Platform",
    #     recipients=[user.mail_id],  # list of email addresses
    #     body=f"""
    #     Hello {user.user_name},

    #     Your account has been created successfully!

    #     Login details:
    #     Email: {user.mail_id}
    #     Password: {user.password}

    #     Regards,
    #     Support Team
    #     """,
    #     subtype="plain"  # can also be "html"
    # )



    # Use shared email service
    email_service = EmailService()
    try:
        login_link = "https://icaptureapp.com/"
        await email_service.send_welcome_email(
            user_name=user.user_name,
            email=user.mail_id,
            password=user.password,
            login_link=login_link ,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
        pass

    return user_id



#update user
async def update_user(request: Request, user_id: int, user: UserUpdate):
    org_id = (
        await admin_repo.get_org_id_by_name(request, user.org_name)
        if user.org_name
        else None
    )
    role_id = user.role_id if user.role_id else None
    await admin_repo.update_user_in_db(request, user_id, user, org_id, role_id)



#Keyword Creation
async def create_keyword(request: Request, keyword: KeywordCreate) -> KeywordMaster:
    try:
        existing_keyword = await admin_repo.get_keyword_by_keyword_name(
            request, keyword.keyword_name,keyword.org_id,keyword.cat_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal error while checking keyword"
        )

    if existing_keyword:
        raise HTTPException(
            status_code=400, detail="keyword already exists with this name"
        )

    try:
        keyword_id = await admin_repo.create_keyword(
            request,
            keyword.keyword_name,
            keyword.org_id,
            keyword.created_by,
            keyword.cat_id,
        )
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Internal error while creating keyword"
        )
    return keyword_id



# update keyword
async def update_keyword(request: Request, keyword: KeywordUpdate) -> KeywordMaster:
    return await admin_repo.update_keyword(request, keyword)



#Login User
async def login_user(request: Request, email: str, password: str) -> dict:
    """
    Authenticate user and return user data with organization and role information
    """
    # Get user data with organization and role names
    user_data = await admin_repo.get_user_by_email(request, email)

    if not user_data:
        raise HTTPException(status_code=400, detail="User not found")

    # Verify password
    if not admin_repo.verify_password(password, user_data["password"]):
        raise HTTPException(status_code=400, detail="Invalid password")

    return user_data


# Fetching the all users on admin dashboard
# async def get_all_users_by_org_id(request: Request,org_id:int,userId:int):
#     try:
#         return await admin_repo.get_all_users_by_org_id(request,org_id,userId)
#     except Exception as e:
#         return None



#listing all users on admin dashboard
async def get_all_users_by_org_id(
    request: Request, org_id: int, userId: int, page: int, limit: int, role_id:int
) -> Dict[str, Any]:
    try:
        result = await admin_repo.get_all_users_by_org_id(
            request, org_id, userId, page, limit, role_id
        )
        return result
    except Exception as e:
        print("Error in service:", e)
        return {"users": [], "totalCount": 0}


# Fetching the all Keywords on admin dashboard
async def get_all_keywords_by_org_id(
    request: Request, org_id: int, userId: int, page: int, limit: int
) -> Dict[str, Any]:
    try:
        result = await admin_repo.get_all_keywords_by_org_id(
            request, org_id, userId, page, limit
        )
        return result
    except Exception as e:
        print("Error in service:", e)
        return {"keywords": [], "totalCount": 0}




# Fetching the all roles in dropdown on create user model
async def get_all_roles(request: Request) -> list[RoleResponse]:
    try:
        roles = await admin_repo.get_all_roles(request)
        return [RoleResponse(**role) for role in roles]
    except Exception as e:
        return None

#listing Category on UI creation of keyword
async def get_all_categories(
    request: Request, userId: int, org_id: int
) -> list[CategoryResponse]:
    try:
        categories = await admin_repo.get_all_categories(request, userId, org_id)
        return [CategoryResponse(**category) for category in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# total effort time on admin dashboard
async def get_total_effort(request, from_date: str, to_date: str, org_id: int):
    try:
        return await AdminRepo.fetch_total_effort(request, from_date, to_date, org_id)
    except Exception as e:
        return None



# total active user on admin dashboard
async def get_active_users(
    request, from_date: str, to_date: str, userId: int, org_id: int, role_id:int
):
    try:
        return await AdminRepo.fetch_active_users(
            request, from_date, to_date, userId, org_id, role_id
        )
    except Exception as e:
        return None



# total email processed on admin dashboard
async def get_emails_processed(request, from_date: str, to_date: str, org_id: int):
    try:
        return await AdminRepo.fetch_emails_processed(
            request, from_date, to_date, org_id
        )
    except Exception as e:
        return None
    
# total meeting processed on admin dashboard 
async def get_meetings_processed(request, from_date: str, to_date: str, org_id: int):
    try:
        return await admin_repo.fetch_meetings_processed(request, from_date, to_date, org_id)
    except Exception as e:
        return None




# total analyzed documents on admin dashboard
async def get_documents_analyzed(request, from_date: str, to_date: str, org_id: int):
    try:
        return await AdminRepo.fetch_documents_analyzed(
            request, from_date, to_date, org_id
        )
    except Exception as e:
        return None



# Getting weekly hours
async def get_weekly_hours_previous_month(
    request, org_id: int,from_date: str,  # Expecting 'YYYY-MM-DD'
    to_date: str 
) -> List[Dict[str, Any]]:
    try:
        return await AdminRepo.get_weekly_hours_previous_month(request, org_id,from_date,to_date)
    except Exception as e:
        return None


# get Top Keywords
async def get_top_keywords(request, org_id: int, user_id: int,from_date:str,to_date:str, limit: int = 5):
    try:
        rows = await AdminRepo.fetch_keywords_by_org(request,org_id, user_id,from_date,to_date )

        # Flatten keywords (split by comma, strip spaces)
        all_keywords = []
        for (kw,) in rows:
            if kw:
                parts = [k.strip().lower() for k in kw.split(",")]
                all_keywords.extend(parts)

        # Count top N
        counter = Counter(all_keywords)
        return counter.most_common(limit)
    except Exception as e:
        return []



    # Update User Status
async def update_user_status(request, user_id: int, is_active: int, org_id: int):
    try:
        return await admin_repo.update_user_status(request, user_id, is_active, org_id)
    except Exception as e:
        return None



# Update Keyword Status
async def update_keyword_status(
    request,
    keyword_id: int,
    is_active: int,
):
    try:
        return await admin_repo.update_keyword_status(request, keyword_id, is_active)
    except Exception as e:
        return None

#find Last sync of each user
async def get_last_sync_by_users(org_id: int,request: Request):
    try:
        last_sync_data = await admin_repo.fetch_last_sync_by_users(org_id,request)
        return last_sync_data
    except Exception as e:
        raise Exception(f"Error fetching last sync data: {str(e)}")
    
    
    
    
    #Check is email is present ?
async def check_email_exists(email: str, request):
    
    # get_user_by_email_id
    user = await get_user_by_email_id(email, request)
    if not user:
        # raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email not found")
        return None
    return user

#Password Reset Based on user id and org id 
async def reset_password(request: Request, user_id: int,  new_password: str) -> bool:
    try:
        # Hash the password
        hashed_pass = AdminRepo.hash_password(new_password)
        
        # Update password in DB
        updated = await update_user_password(user_id, hashed_pass, request)
        if updated is False:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="User not found or org_id mismatch")
        # return updated
        else:
        # Use shared email service
            email_service = EmailService()
            try:
                login_link = "https://icaptureapp.com/"
                await email_service.send_password_changed_email(
                    user_name=updated[2],
                    email=updated[3],
                    login_link=login_link,
                    #password=new_password,#updated[4],
                )

                return True
            except Exception as e:
                print(f"Failed to send email: {e}")
                pass

    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"Password reset failed: {str(e)}")
    
    
    #Search Filetr On User 
async def search_user(request: Request, org_id: int, query: str, page: int, limit: int):
    try:
        users, total = await admin_repo.search_user(request, org_id, query, page, limit)
        return {
            "items": users,               # "items" for frontend
            "totalCount": total,
            "currentPage": page,
            "totalPages": (total + limit - 1) // limit,
        }
    except Exception as e:
        print("Error in search_user service:", e)
        raise

# Search Keywords
async def search_keyword(request, org_id: int, query: str, page: int, limit: int):
    try:
        keywords, total = await admin_repo.search_keyword(request, org_id, query, page, limit)
        return {
            "items": keywords,            # frontend expects 'items'
            "totalCount": total,
            "currentPage": page,
            "totalPages": (total + limit - 1) // limit,  # total is already int
        }
    except Exception as e:
        print("Error in search_keyword service:", e)
        raise
    
    
# Search Categories
async def search_category(request, org_id: int, query: str, page: int, limit: int):
    try:
        categories, total = await admin_repo.search_category(request, org_id, query, page, limit)
        return {
            "categories": categories,
            "totalCount": total,
            "currentPage": page,
            "totalPages": (total + limit - 1) // limit,
        }
    except Exception as e:
        print("Error in search_category service:", e)
        raise

    
   