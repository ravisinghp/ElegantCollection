from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role_id = payload.get("role_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "user_id": user_id,
            "role_id": role_id
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")