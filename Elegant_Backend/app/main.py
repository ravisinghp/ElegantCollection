from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from app.api.routes.EscalationController import router as Escalation_router
from app.services.SystemAdminSchedularService import SchedulerService
import asyncio
 
# --- IMPORTS ---
# 1. Import the Login/Register logic (from authentication.py)
from app.api.routes.authentication import router as auth_router
 
# 2. Import the Admin Dashboard logic (from AdminController.py)
from app.api.routes.AdminController import router as admin_router
 
# 3. Import other API routes
from app.api.routes.api import router as api_router
 
from app.api.routes.UserController import router as user_router
 
# --- CONFIG ---
from app.core.config import ALLOWED_HOSTS, PROJECT_NAME, VERSION, DEBUG
from app.api.errors.http_error import http_error_handler
from app.api.errors.validation_error import http422_error_handler
from app.core.events import create_start_app_handler, create_stop_app_handler
from app.db.mssql import connect_to_mssql, close_mssql_connection
 
 
def get_application() -> FastAPI:
    application = FastAPI(title=PROJECT_NAME, debug=DEBUG, version=VERSION)
 
    # --- CORS CONFIGURATION (FIXED) ---
    # We explicitly define the frontend ports here to ensure they are never blocked.
    # Even if ALLOWED_HOSTS in config is missing 'localhost:5173', this list ensures it works.
    origins = [
        "http://localhost:5173",
        "http://172.105.34.172:5173",

        "http://localhost:3000",
        "http://172.105.34.172:5173",

        "http://localhost:8080",
        "http://172.105.34.172:8080",
    ]
 
    # If your config has extra hosts (like production domains), add them to the list
    if ALLOWED_HOSTS:
        # Ensure ALLOWED_HOSTS is a list before extending

        if isinstance(ALLOWED_HOSTS, list):
            origins.extend(ALLOWED_HOSTS)
        else:
            # If it's a single string, just append it
             origins.append(str(ALLOWED_HOSTS))
 
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,       # Use the robust list we built above
        allow_credentials=True,      # Essential for your Token/Auth to work
        allow_methods=["*"],         # Allow all methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],         # Allow all headers (Authorization, Content-Type, etc.)
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
 
    application.include_router(user_router)
 
    application.include_router(Escalation_router)
 
    application.add_event_handler("startup", create_start_app_handler(application))
    application.add_event_handler("shutdown", create_stop_app_handler(application))
   
    return application
 
 
app = get_application()
 
#For Scheduler get auto start
@app.on_event("startup")
async def startup_event():
    SchedulerService.app = app
    SchedulerService.loop = asyncio.get_running_loop()
    await SchedulerService.configure()

# Ensure async functions run properly on startup/shutdown
@app.on_event("startup")
async def startup_mssql():
    await connect_to_mssql(app)

@app.on_event("shutdown")
async def shutdown_mssql():
    await close_mssql_connection(app)