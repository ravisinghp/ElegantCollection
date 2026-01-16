# app/services/sharepoint_service.py
import aiohttp
from datetime import datetime
from typing import List, Optional
from app.db.repositories.sharepoint_repo import SharepointRepo
import json


class SharepointService:
    def __init__(self, sp_repo: SharepointRepo):
        self.sp_repo = sp_repo
        self.graph_api_base = "https://graph.microsoft.com/v1.0"

    # ---------------- GET SITE ID ---------------- #
    async def get_site_id(self, access_token: str, hostname: str, site_path: str):
        url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise Exception(f"Failed to get site ID: {resp.status} | {text}")
                data = await resp.json()
                return data["id"]


    # ---------------- GET DRIVE ID ---------------- #
    async def get_drive_id(self, access_token: str, site_id: str):
        headers = {"Authorization": f"Bearer {access_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive",
                headers=headers
            ) as resp:

                data = await resp.json()
                if resp.status != 200:
                    raise Exception(f"Failed to get drive: {data}")

                return data["id"]
            

    # ---------------- LIST ALL FOLDERS RECURSIVELY ---------------- #
    async def list_folders_recursive(self, access_token: str, drive_id: str, folder_path: str = ""):
        folders = []

        async def fetch_children(path: str, parent_path: str = ""):
            url = f"{self.graph_api_base}/drives/{drive_id}/root"
            if path:
                url += f":/{path}:/children"
            else:
                url += "/children"

            headers = {"Authorization": f"Bearer {access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to fetch folders recursively: {resp.status}")
                    data = await resp.json()
                    for item in data.get("value", []):
                        if "folder" in item:
                            folder_name = item["name"]
                            full_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                            folders.append({"id": item["id"], "name": folder_name, "path": full_path})
                            await fetch_children(full_path, full_path)

        await fetch_children(folder_path)
        return folders

    # ---------------- FETCH FILES ---------------- #
    async def fetch_drive_files(
        self,
        access_token: str,
        drive_id: str,
        folder_path: Optional[str] = "",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[dict]:
        url = f"{self.graph_api_base}/drives/{drive_id}/root"
        if folder_path:
            url += f":/{folder_path}:/children"
        else:
            url += "/children"

        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to fetch files: {resp.status}")
                data = await resp.json()
                files = data.get("value", [])

        # Filter by date
        if from_date or to_date:
            from_dt = datetime.fromisoformat(from_date) if from_date else None
            to_dt = datetime.fromisoformat(to_date) if to_date else None
            filtered = []
            for f in files:
                created_dt = datetime.fromisoformat(f.get("createdDateTime")[:19])
                if from_dt and created_dt < from_dt:
                    continue
                if to_dt and created_dt > to_dt:
                    continue
                filtered.append(f)
            files = filtered

        return files

    # ---------------- MAIN ORCHESTRATION ---------------- #
    async def fetch_and_save_sharepoint_files(
        self,
        access_token: str,
        user_id: str,
        site_url: str,
        library_name: str,
        folder_path: Optional[str] = "",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ):
        site_id = await self.get_site_id(access_token, site_url)
        drive_id = await self.get_drive_id(access_token, site_id, library_name)
        files = await self.fetch_drive_files(access_token, drive_id, folder_path, from_date, to_date)

        if not files:
            return {"message": "No files found for the given criteria"}

        saved_files = []
        for f in files:
            saved = await self.sp_repo.save_sharepoint_file_metadata(
                user_id=user_id,
                file_name=f.get("name"),
                file_url=f.get("webUrl"),
                created_date=f.get("createdDateTime"),
                modified_date=f.get("lastModifiedDateTime"),
                folder_path=folder_path or "",
            )
            saved_files.append(saved)

        return {"saved_count": len(saved_files), "files": saved_files}