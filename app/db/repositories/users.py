from typing import Optional, Any, List
from app.db.errors import EntityDoesNotExist
from app.db.repositories.base import BaseRepository
from app.models.domain.users import User, UserInDB,file_list
import datetime
from loguru import logger

GET_USER_BY_EMAIL_QUERY = """
SELECT user_id,
       user_name,
       mail_id,
       password,
       org_id,
       role_id,
       folder_name,
       created_on,
       updated_on,
       is_active
FROM users_master
WHERE mail_id = %s
"""

GET_USER_BY_USERNAME_QUERY = """
SELECT id,
       username,
       email,
       salt,
       hashed_password,
       bio,
       image,
       created_at,
       updated_at
FROM users
WHERE username = %s
"""

GET_ALL_USERS_QUERY = """
SELECT id,
       file_name,
       file_type,
       contract_type_id,
       status_id,
       status_message,
       risk_score
FROM res_files
"""

CREATE_USER_QUERY = """
INSERT INTO users (username, email, salt, hashed_password)
VALUES (%s, %s, %s, %s)
"""

UPDATE_USER_QUERY = """
UPDATE users
SET username        = %s,
    email           = %s,
    salt            = %s,
    hashed_password = %s,
    bio             = %s,
    image           = %s,
    updated_at      = %s
WHERE username = %s
"""


class UsersRepository(BaseRepository):
    async def get_user_by_email(self, *, email: str) -> UserInDB:
        user_row = await self._log_and_fetch_one(GET_USER_BY_EMAIL_QUERY, email)
        if user_row:
            return UserInDB(**user_row)

        raise EntityDoesNotExist(f"user with email {email} does not exist")
    
    async def get_all_users(self) -> List[file_list]:
        users_rows = await self._log_and_fetch_all(GET_ALL_USERS_QUERY)
        if users_rows:
            # Ensure that the keys in the user_row dictionary match the fields in the User model
            return [file_list(
                id=user_row['id'],
                fileName=user_row['file_name'],
                fileType=user_row['file_type'],
                contractTypeId=user_row['contract_type_id'],
                statusId=user_row['status_id'],
                status_message=user_row['status_message'],
                riskScore=user_row['risk_score'],
            ) for user_row in users_rows]
        raise EntityDoesNotExist("No users found in the database")




    async def get_user_by_username(self, *, username: str) -> UserInDB:
        user_row = await self._log_and_fetch_one(GET_USER_BY_USERNAME_QUERY, username)
        if user_row:
            return UserInDB(**user_row)

        raise EntityDoesNotExist(f"user with username {username} does not exist")

    async def create_user(
        self, *, username: str, email: str, password: str
    ) -> UserInDB:
        user = UserInDB(username=username, email=email)
        user.change_password(password)

        await self._log_and_execute(
            CREATE_USER_QUERY,
            [user.username, user.email, user.salt, user.hashed_password],
        )

        user_row = await self._log_and_fetch_one(
            GET_USER_BY_USERNAME_QUERY, user.username
        )

        return user.copy(update=dict(user_row))

    async def update_user(
        self,
        *,
        user: User,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        bio: Optional[str] = None,
        image: Optional[str] = None,
    ) -> UserInDB:
        user_in_db = await self.get_user_by_username(username=user.username)

        user_in_db.username = username or user_in_db.username
        user_in_db.email = email or user_in_db.email
        user_in_db.bio = bio or user_in_db.bio
        user_in_db.image = image or user_in_db.image
        if password:
            user_in_db.change_password(password)

        now = datetime.datetime.now()
        user_in_db.updated_at = now.strftime("%Y-%m-%d %H:%M:%S")

        await self._log_and_execute(
            UPDATE_USER_QUERY,
            [
                user_in_db.username,
                user_in_db.email,
                user_in_db.salt,
                user_in_db.hashed_password,
                user_in_db.bio,
                user_in_db.image,
                user_in_db.updated_at,
                user.username,
            ],
        )

        return user_in_db
