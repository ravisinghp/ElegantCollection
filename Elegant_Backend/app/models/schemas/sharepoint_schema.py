from pydantic import BaseModel

class FolderRequestParams(BaseModel):
  user_id: int