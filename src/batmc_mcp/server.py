"""FastMCP server instance with lifespan-managed auth and HTTP client."""
import sys
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
from fastmcp import FastMCP

from batmc_mcp.config import get_config, MCPConfig
from batmc_mcp.auth import AuthManager
from batmc_mcp.api_client import APIClient

# ALL logging to stderr (stdio transport uses stdout for protocol)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("batmc_mcp")


@dataclass
class AppContext:
    api: APIClient
    config: MCPConfig


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    config = get_config()
    logger.info(f"Starting BATMC MCP server (env={config.env})")

    auth = AuthManager(
        supabase_url=config.supabase_url,
        anon_key=config.supabase_anon_key,
        email=config.user_email,
        password=config.user_password,
    )
    await auth.login()
    logger.info(f"Authenticated as {config.user_name}")

    http_client = httpx.AsyncClient(
        base_url=config.api_url,
        timeout=httpx.Timeout(60.0, connect=10.0),
    )

    # Wake up Render if sleeping
    try:
        r = await http_client.get("/ping", headers=await auth.get_headers())
        logger.info(f"API ping: {r.status_code}")
    except Exception as e:
        logger.warning(f"API ping failed (may be cold starting): {e}")

    api = APIClient(http_client=http_client, auth=auth)

    try:
        yield AppContext(api=api, config=config)
    finally:
        await http_client.aclose()
        logger.info("MCP server shutdown")


mcp = FastMCP("BATMC Lending", lifespan=app_lifespan)

# Import tools to register them
import batmc_mcp.tools.borrowers  # noqa: F401
# import batmc_mcp.tools.loans      # noqa: F401  (Plan 03)
# import batmc_mcp.tools.payments   # noqa: F401  (Plan 03)
