import logging
import sys
from typing import List

from databases import DatabaseURL
from loguru import logger
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

from app.core.logging import InterceptHandler
# ADD THIS LINE:
ALGORITHM = "HS256"
API_PREFIX = "/api"

JWT_TOKEN_PREFIX = "Token"  
VERSION = "1.0.0"

config = Config(".env")

DEBUG: bool = config("DEBUG", cast=bool, default=False)

DATABASE_URL: DatabaseURL = config("DB_CONNECTION", cast=DatabaseURL)
MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)
HOST:str = config("HOST",cast=str,default="127.0.0.1")
PORT:int = config("PORT",cast=int,default=3306)
USER:str = config("USER",cast=str,default="root")
PWD:str = config("PWD",cast=str,default="")
DB:str = config("DB",cast=str,default="")

# ----------------- EMR Database Config start------------------#
MSSQL_HOST: str = config("MSSQL_HOST", cast=str, default="localhost")
MSSQL_PORT: int = config("MSSQL_PORT", cast=int, default=1433)
MSSQL_USER: str = config("MSSQL_USER", cast=str, default="sa")
MSSQL_PWD: str = config("MSSQL_PWD", cast=str, default="")
MSSQL_DB: str = config("MSSQL_DB", cast=str, default="")

SECRET_KEY: Secret = config("SECRET_KEY", cast=Secret)

PROJECT_NAME: str = config("PROJECT_NAME", default="FastAPI example application")
ALLOWED_HOSTS: List[str] = config(
    "ALLOWED_HOSTS", cast=CommaSeparatedStrings, default=""
)

# logging configuration

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    handlers=[InterceptHandler(level=LOGGING_LEVEL)], level=LOGGING_LEVEL
)
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])
