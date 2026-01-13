from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

SECRET_KEY = str(config.SECRET_KEY)

ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print("TOKEN RECEIVED:", token)  
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("JWT PAYLOAD:", payload)
        user_name = payload.get("username")
        user_id = payload.get("userid")
        role_id = payload.get("roleid")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "user_id": user_id,
            "role_id": role_id,
            "user_name":user_name
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")