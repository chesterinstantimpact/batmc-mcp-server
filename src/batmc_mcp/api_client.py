"""Typed HTTP client wrapper with auth injection and 401 retry."""
import logging

import httpx

from batmc_mcp.auth import AuthManager

logger = logging.getLogger("batmc_mcp.api_client")


class APIClient:
    """HTTP client wrapper that injects auth headers and handles 401 retry."""

    def __init__(self, http_client: httpx.AsyncClient, auth: AuthManager):
        self.http = http_client
        self.auth = auth

    async def get(self, path: str, params: dict | None = None) -> httpx.Response:
        """Send GET request with auth headers, retrying on 401."""
        headers = await self.auth.get_headers()
        response = await self.http.get(path, params=params, headers=headers)
        if response.status_code == 401:
            logger.info("Got 401, refreshing token and retrying")
            await self.auth.refresh()
            headers = await self.auth.get_headers()
            response = await self.http.get(path, params=params, headers=headers)
        return response

    async def post(self, path: str, json: dict | None = None) -> httpx.Response:
        """Send POST request with auth headers, retrying on 401."""
        headers = await self.auth.get_headers()
        response = await self.http.post(path, json=json, headers=headers)
        if response.status_code == 401:
            logger.info("Got 401, refreshing token and retrying")
            await self.auth.refresh()
            headers = await self.auth.get_headers()
            response = await self.http.post(path, json=json, headers=headers)
        return response

    async def put(self, path: str, json: dict | None = None) -> httpx.Response:
        """Send PUT request with auth headers, retrying on 401."""
        headers = await self.auth.get_headers()
        response = await self.http.put(path, json=json, headers=headers)
        if response.status_code == 401:
            logger.info("Got 401, refreshing token and retrying")
            await self.auth.refresh()
            headers = await self.auth.get_headers()
            response = await self.http.put(path, json=json, headers=headers)
        return response

    async def delete(self, path: str) -> httpx.Response:
        """Send DELETE request with auth headers, retrying on 401."""
        headers = await self.auth.get_headers()
        response = await self.http.delete(path, headers=headers)
        if response.status_code == 401:
            logger.info("Got 401, refreshing token and retrying")
            await self.auth.refresh()
            headers = await self.auth.get_headers()
            response = await self.http.delete(path, headers=headers)
        return response
