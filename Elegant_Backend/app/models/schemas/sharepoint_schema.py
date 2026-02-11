from pydantic import BaseModel

class FolderRequestParams(BaseModel):
  user_id: int
  site_id: str
  
class SharepointSitesRequest(BaseModel):
    user_id: int
    
