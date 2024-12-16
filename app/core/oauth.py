# OAuth implementation

from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings


async def verify_google_token(token: str) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid issuer')

        return idinfo
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")
