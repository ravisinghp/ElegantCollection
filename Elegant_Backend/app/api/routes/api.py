from fastapi import APIRouter

from app.api.routes import authentication, users
from app.api.routes import authentication, users, report_data
from app.api.routes.AdminController import router as admin_router
from app.api.routes.UserController import router as user_router
from app.api.routes.SystemAdminSchedular import router as SystemAdmin_router
from app.api.routes import category_section


router = APIRouter()
router.include_router(authentication.router, tags=["authentication"], prefix="/users")
# router.include_router(users.router, tags=["users"], prefix="/user")
# Alias routes for clients calling /auth/* instead of /user/*
router.include_router(users.router, tags=["users"], prefix="/auth")
router.include_router(report_data.router, tags=["report_data"], prefix="/reports")
router.include_router(admin_router, tags=["admin"], prefix="/admin")
router.include_router(user_router, tags=["userdash"], prefix="/userdash")
router.include_router(
    category_section.router, tags=["categories"], prefix="/categories"
)
router.include_router(SystemAdmin_router, tags=["SystemAdmin"], prefix="/systemadmin")
# Include user router
# router.include_router(auth.router, prefix="/auth", tags=["auth"])
