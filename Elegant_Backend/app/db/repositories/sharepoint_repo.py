# app/db/repositories/sharepoint_repo.py
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
# from app.db.tables import sharepoint_files_table  # SQLAlchemy table for SharePoint files


class SharepointRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------------- SAVE FILE METADATA ---------------- #
    # async def save_sharepoint_file_metadata(
    #     self,
    #     user_id: str,
    #     file_name: str,
    #     file_url: str,
    #     created_date: str,
    #     modified_date: str,
    #     folder_path: str,
    # ) -> Dict[str, Any]:
    #     """
    #     Save SharePoint file metadata to DB.
    #     Returns the saved record.
    #     """
    #     query = insert(sharepoint_files_table).values(
    #         user_id=user_id,
    #         file_name=file_name,
    #         file_url=file_url,
    #         created_date=created_date,
    #         modified_date=modified_date,
    #         folder_path=folder_path,
    #     ).returning(*sharepoint_files_table.c)

    #     result = await self.session.execute(query)
    #     await self.session.commit()

    #     return dict(result.fetchone())

    # # ---------------- GET FILES FOR USER ---------------- #
    # async def get_files_by_user(self, user_id: str):
    #     """
    #     Get all SharePoint files fetched for a user.
    #     """
    #     query = select(sharepoint_files_table).where(
    #         sharepoint_files_table.c.user_id == user_id
    #     )
    #     result = await self.session.execute(query)
    #     return [dict(row) for row in result.fetchall()]

    # # Optional: get files in folder
    # async def get_files_by_folder(self, user_id: str, folder_path: str):
    #     query = select(sharepoint_files_table).where(
    #         sharepoint_files_table.c.user_id == user_id,
    #         sharepoint_files_table.c.folder_path == folder_path
    #     )
    #     result = await self.session.execute(query)
    #     return [dict(row) for row in result.fetchall()]
