"""MCP tools for payment operations."""

import logging

from fastmcp.server.context import Context

from batmc_mcp.server import mcp, AppContext
from batmc_mcp.formatting import format_payment_response

logger = logging.getLogger("batmc_mcp.tools.payments")


def _get_app(ctx: Context) -> AppContext:
    """Extract AppContext from the MCP request context."""
    return ctx.request_context.lifespan_context


def _extract_error(response) -> str:
    """Extract error detail from an API response."""
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        detail = response.json().get("detail", response.text)
    else:
        detail = response.text
    return f"Error ({response.status_code}): {detail}"


@mcp.tool()
async def record_payment(
    payment_date: str,
    total_amount: str,
    allocations: list[dict],
    allow_overpayment: bool = False,
    notes: str | None = None,
    ctx: Context = None,
) -> str:
    """Record a payment against one or more loans.

    payment_date in YYYY-MM-DD format. total_amount as string (e.g., '5000').
    allocations is a list of {'loan_id': 'uuid', 'amount': 'string'} objects.
    The sum of allocation amounts must equal total_amount.

    Example:
        record_payment(
            payment_date="2025-12-15",
            total_amount="5000",
            allocations=[{"loan_id": "abc-123", "amount": "5000"}],
        )
    """
    app = _get_app(ctx)

    payload = {
        "payment_date": payment_date,
        "total_amount": total_amount,
        "allocations": [
            {"loan_id": a["loan_id"], "amount": a["amount"]}
            for a in allocations
        ],
        "allow_overpayment": allow_overpayment,
    }
    if notes:
        payload["notes"] = notes

    response = await app.api.post("/api/payments", json=payload)

    if response.status_code == 201:
        return format_payment_response(response.json())
    elif response.status_code == 400:
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            detail = response.json().get("detail", response.text)
        else:
            detail = response.text
        return f"Payment rejected: {detail}"
    else:
        return _extract_error(response)
