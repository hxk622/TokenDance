"""WeChat OAuth service for WeChat login."""
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User, AuthProvider

logger = get_logger(__name__)


class WeChatOAuthService:
    """Service for WeChat OAuth authentication."""

    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.app_secret = settings.WECHAT_APP_SECRET
        self.base_url = "https://open.weixin.qq.com"
        self.api_url = "https://api.weixin.qq.com"

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate WeChat OAuth authorization URL.
        
        Args:
            redirect_uri: Callback URL after authorization
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        params = {
            "appid": self.app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "snsapi_login",
        }
        
        if state:
            params["state"] = state
        else:
            params["state"] = "wechat"
        
        return f"{self.base_url}/connect/qrconnect?" + "&".join(
            f"{k}={v}" for k, v in params.items()
        )

    async def get_access_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from WeChat
            
        Returns:
            Token response dict or None if failed
        """
        url = f"{self.api_url}/sns/oauth2/access_token"
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if "errcode" in data:
                    logger.error(
                        "wechat_oauth_token_error",
                        errcode=data.get("errcode"),
                        errmsg=data.get("errmsg"),
                    )
                    return None
                
                return data
        except Exception as e:
            logger.error("wechat_oauth_token_exception", error=str(e))
            return None

    async def get_user_info(
        self,
        access_token: str,
        openid: str
    ) -> Optional[Dict[str, Any]]:
        """Get user information from WeChat.
        
        Args:
            access_token: WeChat access token
            openid: WeChat OpenID
            
        Returns:
            User info dict or None if failed
        """
        url = f"{self.api_url}/sns/userinfo"
        params = {
            "access_token": access_token,
            "openid": openid,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if "errcode" in data:
                    logger.error(
                        "wechat_oauth_userinfo_error",
                        errcode=data.get("errcode"),
                        errmsg=data.get("errmsg"),
                    )
                    return None
                
                return data
        except Exception as e:
            logger.error("wechat_oauth_userinfo_exception", error=str(e))
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh WeChat access token.
        
        Args:
            refresh_token: WeChat refresh token
            
        Returns:
            New token response dict or None if failed
        """
        url = f"{self.api_url}/sns/oauth2/refresh_token"
        params = {
            "appid": self.app_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if "errcode" in data:
                    logger.error(
                        "wechat_oauth_refresh_error",
                        errcode=data.get("errcode"),
                        errmsg=data.get("errmsg"),
                    )
                    return None
                
                return data
        except Exception as e:
            logger.error("wechat_oauth_refresh_exception", error=str(e))
            return None

    def generate_username(self, wechat_nickname: Optional[str] = None) -> str:
        """Generate a unique username from WeChat nickname.
        
        Args:
            wechat_nickname: WeChat nickname
            
        Returns:
            Unique username
        """
        import random
        import string
        
        base = wechat_nickname or "wx_user"
        
        # Remove special characters and limit length
        base = "".join(c for c in base if c.isalnum() or c == "_")[:20]
        
        # Add random suffix for uniqueness
        suffix = "".join(random.choices(string.digits, k=6))
        return f"{base}_{suffix}"

    def generate_email(self, openid: str) -> str:
        """Generate a unique email from WeChat OpenID.
        
        Args:
            openid: WeChat OpenID
            
        Returns:
            Unique email
        """
        return f"wx_{openid[:8]}@wechat.local"
