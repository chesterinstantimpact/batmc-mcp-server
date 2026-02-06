"""Supabase JWT token management with automatic refresh."""
import time
import logging

import httpx

logger = logging.getLogger("batmc_mcp.auth")


class AuthManager:
    """Manage Supabase JWT tokens with login, refresh, and header injection."""

    def __init__(self, supabase_url: str, anon_key: str, email: str, password: str):
        self.supabase_url = supabase_url
        self.anon_key = anon_key
        self.email = email
        self.password = password
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.expires_at: float = 0

    async def login(self):
        """Initial login via email/password."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/auth/v1/token?grant_type=password",
                json={"email": self.email, "password": self.password},
                headers={"apikey": self.anon_key, "Content-Type": "application/json"},
            )
            response.raise_for_status()
            self._update_tokens(response.json())
        logger.info("Logged in successfully")

    async def refresh(self):
        """Refresh JWT using refresh token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/auth/v1/token?grant_type=refresh_token",
                json={"refresh_token": self.refresh_token},
                headers={"apikey": self.anon_key, "Content-Type": "application/json"},
            )
            response.raise_for_status()
            self._update_tokens(response.json())
        logger.info("Token refreshed")

    async def get_headers(self) -> dict[str, str]:
        """Get auth headers, refreshing if needed."""
        if time.time() >= self.expires_at:
            await self.refresh()
        return {"Authorization": f"Bearer {self.access_token}"}

    def _update_tokens(self, data: dict):
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_at = time.time() + data["expires_in"] - 60  # 1 min buffer
