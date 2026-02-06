"""MCP tools for borrower operations."""

import logging

from fastmcp.server.context import Context

from batmc_mcp.server import mcp, AppContext
from batmc_mcp.formatting import (
    format_borrower_balance_list,
    format_borrower_created,
    format_borrower_list,
)

logger = logging.getLogger("batmc_mcp.tools.borrowers")


def _get_app(ctx: Context) -> AppContext:
    """Extract AppContext from the MCP request context."""
    return ctx.request_context.lifespan_context


@mcp.tool()
async def find_borrower(name: str, ctx: Context) -> str:
    """Search for a borrower by name (partial, case-insensitive match).

    Returns up to 10 matching borrowers with ID, name, phone, and active loan count.
    """
    app = _get_app(ctx)
    response = await app.api.get(
        "/api/borrowers",
        params={"limit": 100, "sort_by": "name", "sort_order": "asc"},
    )

    if response.status_code != 200:
        return f"Error ({response.status_code}): {response.json().get('detail', response.text)}"

    data = response.json()
    all_borrowers = data.get("items", [])

    # Client-side partial name matching (case-insensitive)
    search_lower = name.lower()
    matches = [
        b for b in all_borrowers if search_lower in b.get("name", "").lower()
    ][:10]

    if not matches:
        return f"No borrowers found matching '{name}'"

    return format_borrower_list(matches)


@mcp.tool()
async def list_borrowers(
    active_only: bool = True, page: int = 1, ctx: Context = None
) -> str:
    """List borrowers with their current outstanding balances.

    By default shows only borrowers with active loans, including principal,
    total paid, and remaining balance for each.

    Set active_only=False to list all borrowers (without balance details).
    """
    app = _get_app(ctx)

    if active_only:
        response = await app.api.get("/api/reports/borrowers")
        if response.status_code != 200:
            return f"Error ({response.status_code}): {response.json().get('detail', response.text)}"

        data = response.json()
        return format_borrower_balance_list(data.get("borrowers", []))
    else:
        response = await app.api.get(
            "/api/borrowers",
            params={
                "limit": 50,
                "page": page,
                "sort_by": "name",
                "sort_order": "asc",
            },
        )
        if response.status_code != 200:
            return f"Error ({response.status_code}): {response.json().get('detail', response.text)}"

        data = response.json()
        borrowers = data.get("items", [])
        total = data.get("total", 0)
        pages = data.get("pages", 1)

        result = format_borrower_list(borrowers)
        if pages > 1:
            result += f"\n\nPage {page} of {pages} (total: {total})"
        return result


@mcp.tool()
async def create_borrower(
    name: str, phone: str, address: str | None = None, ctx: Context = None
) -> str:
    """Create a new borrower. Name and phone are required. Address is optional.

    Example: create_borrower(name="Juan Dela Cruz", phone="09171234567")
    """
    app = _get_app(ctx)

    body = {"name": name, "phone": phone}
    if address is not None:
        body["address"] = address

    response = await app.api.post("/api/borrowers", json=body)

    if response.status_code == 201:
        return format_borrower_created(response.json())
    elif response.status_code == 422:
        errors = response.json()
        detail = errors.get("detail", errors)
        if isinstance(detail, list):
            messages = [
                f"  - {e.get('loc', ['?'])[-1]}: {e.get('msg', '?')}"
                for e in detail
            ]
            return "Validation error:\n" + "\n".join(messages)
        return f"Validation error: {detail}"
    else:
        return f"Error ({response.status_code}): {response.json().get('detail', response.text)}"
