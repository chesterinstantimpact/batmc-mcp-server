"""Shared formatting helpers for human-readable MCP tool output."""

from decimal import Decimal, InvalidOperation


def format_money(amount) -> str:
    """Format a number/string as Philippine Peso: 'P1,000.00'.

    Handles Decimal strings, floats, ints, and None.
    """
    if amount is None:
        return "P0.00"
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return f"P{amount}"
    return f"P{value:,.2f}"


def format_borrower_list(borrowers: list[dict]) -> str:
    """Format a list of borrowers for LLM display.

    Each borrower shows: name, phone, active loan count. Numbered list.
    Returns 'No borrowers found.' if the list is empty.
    """
    if not borrowers:
        return "No borrowers found."

    lines = [f"Borrowers ({len(borrowers)}):"]
    lines.append("")
    for i, b in enumerate(borrowers, 1):
        name = b.get("name", "Unknown")
        phone = b.get("phone", "N/A")
        active_loans = b.get("active_loan_count", 0)
        borrower_id = b.get("id", "")
        lines.append(f"  {i}. {name}")
        lines.append(f"     Phone: {phone} | Active loans: {active_loans}")
        lines.append(f"     ID: {borrower_id}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_borrower_balance_list(borrowers: list[dict]) -> str:
    """Format borrowers with balance info for LLM display.

    Each shows: name, total principal, total paid, remaining balance, active loans.
    Includes a total row at bottom summing remaining_balance.
    """
    if not borrowers:
        return "No borrowers with active loans found."

    # Count total borrowers (the report endpoint only returns those with active loans)
    total_outstanding = Decimal("0")
    lines = [f"Borrowers with Active Loans ({len(borrowers)}):"]
    lines.append("")

    for i, b in enumerate(borrowers, 1):
        name = b.get("borrower_name", "Unknown")
        principal = b.get("total_principal", 0)
        paid = b.get("total_paid", 0)
        balance = b.get("remaining_balance", 0)
        active_loans = b.get("active_loan_count", 0)

        total_outstanding += Decimal(str(balance))

        lines.append(f"  {i}. {name}")
        lines.append(
            f"     Principal: {format_money(principal)} | "
            f"Paid: {format_money(paid)} | "
            f"Balance: {format_money(balance)}"
        )
        lines.append(f"     Active loans: {active_loans}")
        lines.append("")

    lines.append("---")
    lines.append(f"Total Outstanding: {format_money(total_outstanding)}")

    return "\n".join(lines)


def format_borrower_detail(borrower: dict) -> str:
    """Format a single borrower with their loans.

    Shows: name, phone, address, then list of loans with id, principal, date, status.
    """
    name = borrower.get("name", "Unknown")
    phone = borrower.get("phone", "N/A")
    address = borrower.get("address") or "N/A"
    borrower_id = borrower.get("id", "")

    lines = [f"Borrower: {name}"]
    lines.append(f"  Phone: {phone}")
    lines.append(f"  Address: {address}")
    lines.append(f"  ID: {borrower_id}")

    loans = borrower.get("loans", [])
    if loans:
        lines.append("")
        lines.append(f"  Loans ({len(loans)}):")
        for loan in loans:
            loan_id = loan.get("id", "")
            principal = loan.get("principal", 0)
            loan_date = loan.get("loan_date", "N/A")
            status = loan.get("status", "unknown")
            lines.append(
                f"    - {format_money(principal)} on {loan_date} "
                f"[{status}] (ID: {loan_id})"
            )
    else:
        lines.append("")
        lines.append("  No loans on record.")

    return "\n".join(lines)


def format_borrower_created(borrower: dict) -> str:
    """Format confirmation after creating a borrower.

    Shows: name, phone, id.
    """
    name = borrower.get("name", "Unknown")
    phone = borrower.get("phone", "N/A")
    borrower_id = borrower.get("id", "")

    return (
        f"Borrower created successfully.\n"
        f"  Name: {name}\n"
        f"  Phone: {phone}\n"
        f"  ID: {borrower_id}"
    )
