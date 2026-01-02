# models/outlook_token.py
from datetime import datetime

class OutlookToken:
    def __init__(self, access_token: str, refresh_token: str, token_expiry: datetime):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = token_expiry
