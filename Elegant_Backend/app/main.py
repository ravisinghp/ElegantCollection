from fastapi import FastAPI
from app.routers import  auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include user router
app.include_router(auth.router, prefix="/auth", tags=["auth"])
# app.include_router(recommended_jobs.router, prefix="/jobs", tags=["Recommended Jobs"])
