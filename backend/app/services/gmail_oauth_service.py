"""Gmail OAuth service for Google login."""
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GmailOAuthService:
    """Service for Gmail OAuth authentication."""

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GMAIL_REDIRECT_URI
        self.scopes = settings.GMAIL_SCOPES.split(",")
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Gmail OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
        }
        
        if state:
            params["state"] = state
        else:
            params["state"] = "gmail"
        
        return f"{self.auth_url}?" + "&".join(
            f"{k}={v}" for k, v in params.items()
        )

    async def get_access_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Token response dict or None if failed
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data, timeout=10.0)
                response.raise_for_status()
                token_data = response.json()
                
                if "error" in token_data:
                    logger.error(
                        "gmail_oauth_token_error",
                        error=token_data.get("error"),
                        error_description=token_data.get("error_description"),
                    )
                    return None
                
                return token_data
        except Exception as e:
            logger.error("gmail_oauth_token_exception", error=str(e))
            return None

    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Google.
        
        Args:
            access_token: Google access token
            
        Returns:
            User info dict or None if failed
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.userinfo_url, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    logger.error(
                        "gmail_oauth_userinfo_error",
                        error=data.get("error"),
                        error_description=data.get("error_description"),
                    )
                    return None
                
                return data
        except Exception as e:
            logger.error("gmail_oauth_userinfo_exception", error=str(e))
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Gmail access token.
        
        Args:
            refresh_token: Gmail refresh token
            
        Returns:
            New token response dict or None if failed
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data, timeout=10.0)
                response.raise_for_status()
                token_data = response.json()
                
                if "error" in token_data:
                    logger.error(
                        "gmail_oauth_refresh_error",
                        error=token_data.get("error"),
                        error_description=token_data.get("error_description"),
                    )
                    return None
                
                return token_data
        except Exception as e:
            logger.error("gmail_oauth_refresh_exception", error=str(e))
            return None

    def generate_username(self, gmail_name: Optional[str] = None, gmail_email: Optional[str] = None) -> str:
        """Generate a unique username from Gmail info.
        
        Args:
            gmail_name: Gmail name
            gmail_email: Gmail email
            
        Returns:
            Unique username
        """
        import random
        import string
        
        base = gmail_name or gmail_email.split("@")[0] if gmail_email else "gmail_user"
        
        # Remove special characters and limit length
        base = "".join(c for c in base if c.isalnum() or c == "_")[:20]
        
        # Add random suffix for uniqueness
        suffix = "".join(random.choices(string.digits, k=6))
        return f"{base}_{suffix}"
