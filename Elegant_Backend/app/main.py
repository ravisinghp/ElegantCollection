from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

# --- IMPORTS ---
# 1. Import the Login/Register logic (from authentication.py)
from app.api.routes.authentication import router as auth_router

# 2. Import the Admin Dashboard logic (from AdminController.py)
from app.api.routes.AdminController import router as admin_router

# 3. Import other API routes
from app.api.routes.api import router as api_router

# --- CONFIG ---
from app.core.config import ALLOWED_HOSTS, PROJECT_NAME, VERSION, DEBUG
from app.api.errors.http_error import http_error_handler
from app.api.errors.validation_error import http422_error_handler
from app.core.events import create_start_app_handler, create_stop_app_handler


def get_application() -> FastAPI:
    application = FastAPI(title=PROJECT_NAME, debug=DEBUG, version=VERSION)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_HOSTS or ["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_event_handler("startup", create_start_app_handler(application))
    application.add_event_handler("shutdown", create_stop_app_handler(application))

    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(RequestValidationError, http422_error_handler)

    # --- REGISTER ROUTES ---
    
    # 1. This enables localhost:8080/login
    application.include_router(auth_router)

    # 2. This enables localhost:8080/admin/createUser (and other admin routes)
    application.include_router(admin_router, prefix="/admin")

    # 3. Other API routes
    application.include_router(api_router)

    return application


app = get_application()