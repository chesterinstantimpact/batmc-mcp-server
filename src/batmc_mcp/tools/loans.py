"""MCP tools for loan operations."""

import logging

from fastmcp.server.context import Context

from batmc_mcp.server import mcp, AppContext
from batmc_mcp.formatting import (
    format_loan_balance,
    format_loan_created,
    format_loan_list,
)

logger = logging.getLogger("batmc_mcp.tools.loans")


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
async def list_loans(
    borrower_name: str | None = None,
    status: str | None = None,
    include_closed: bool = False,
    ctx: Context = None,
) -> str:
    """List loans with optional filters.

    Can filter by borrower name (partial match) and loan status
    (active, paid_off, renewed). Default shows only active loans.
    """
    app = _get_app(ctx)

    loans = []

    if borrower_name:
        # Find borrower(s) by name first
        response = await app.api.get(
            "/api/borrowers",
            params={"limit": 100, "sort_by": "name", "sort_order": "asc"},
        )
        if response.status_code != 200:
            return _extract_error(response)

        all_borrowers = response.json().get("items", [])
        search_lower = borrower_name.lower()
        matches = [
            b
            for b in all_borrowers
            if search_lower in b.get("name", "").lower()
        ]

        if not matches:
            return f"No borrower found matching '{borrower_name}'"

        if len(matches) > 1:
            names = "\n".join(
                f"  - {b.get('name', '')} (ID: {b.get('id', '')})"
                for b in matches[:10]
            )
            return (
                f"Multiple borrowers match '{borrower_name}'. "
                f"Please be more specific:\n{names}"
            )

        # Exactly one match - get their loans via borrower detail
        borrower = matches[0]
        detail_resp = await app.api.get(
            f"/api/borrowers/{borrower['id']}"
        )
        if detail_resp.status_code != 200:
            return _extract_error(detail_resp)

        detail = detail_resp.json()
        borrower_loans = detail.get("loans", [])

        # Enrich each loan summary with borrower info
        for loan in borrower_loans:
            loan["borrower_id"] = borrower["id"]
            loan["borrower_name"] = borrower.get("name", "")
        loans = borrower_loans

    else:
        # No borrower filter - get all loans
        response = await app.api.get(
            "/api/loans",
            params={
                "limit": 100,
                "include_closed": str(include_closed).lower(),
                "sort_by": "loan_date",
                "sort_order": "desc",
            },
        )
        if response.status_code != 200:
            return _extract_error(response)

        loans = response.json().get("items", [])

    # Apply status filter client-side if provided
    if status:
        status_lower = status.lower()
        loans = [
            loan for loan in loans
            if loan.get("status", "").lower() == status_lower
        ]

    # Get balance data for enrichment
    borrower_balances = {}
    try:
        balance_resp = await app.api.get("/api/reports/borrowers")
        if balance_resp.status_code == 200:
            for b in balance_resp.json().get("borrowers", []):
                borrower_balances[b["borrower_id"]] = b
    except Exception as exc:
        logger.warning("Failed to fetch balance data: %s", exc)

    return format_loan_list(loans, borrower_balances)


@mcp.tool()
async def get_loan_balance(loan_id: str, ctx: Context = None) -> str:
    """Get the current balance for a specific loan.

    Shows remaining principal, total paid, and loan status.
    The loan_id should be a UUID (full or partial from a previous listing).
    """
    app = _get_app(ctx)

    # Get loan detail
    response = await app.api.get(f"/api/loans/{loan_id}")
    if response.status_code == 404:
        return "Loan not found."
    if response.status_code != 200:
        return _extract_error(response)

    loan_data = response.json()
    borrower_id = loan_data.get("borrower_id", "")

    # Get balance data from reports endpoint
    balance_data = {}
    balance_resp = await app.api.get("/api/reports/borrowers")
    if balance_resp.status_code == 200:
        for b in balance_resp.json().get("borrowers", []):
            if b.get("borrower_id") == borrower_id:
                balance_data = b
                break

    if not balance_data:
        # Borrower has no active loans in report (loan may be paid off / renewed)
        balance_data = {
            "borrower_name": "",
            "remaining_balance": 0,
            "total_paid": 0,
            "active_loan_count": 0,
        }

    return format_loan_balance(loan_data, balance_data)


@mcp.tool()
async def create_loan(
    borrower_id: str,
    principal: str,
    loan_date: str,
    interest_charge_day: int,
    funding_source_type: str = "cashflow",
    external_funder_name: str | None = None,
    previous_loan_id: str | None = None,
    ctx: Context = None,
) -> str:
    """Create a new loan for a borrower.

    Principal should be a string amount (e.g., '50000'). Loan date in
    YYYY-MM-DD format. Interest charge day is 1-31. Funding defaults to
    'cashflow'; use 'external_person' with external_funder_name for
    external funding.
    """
    app = _get_app(ctx)

    funding_source = {
        "source_type": funding_source_type,
        "amount": principal,
    }
    if external_funder_name:
        funding_source["external_funder_name"] = external_funder_name

    payload = {
        "borrower_id": borrower_id,
        "principal": principal,
        "loan_date": loan_date,
        "interest_charge_day": interest_charge_day,
        "funding_sources": [funding_source],
    }
    if previous_loan_id:
        payload["previous_loan_id"] = previous_loan_id

    response = await app.api.post("/api/loans", json=payload)

    if response.status_code == 201:
        return format_loan_created(response.json())
    else:
        return _extract_error(response)
