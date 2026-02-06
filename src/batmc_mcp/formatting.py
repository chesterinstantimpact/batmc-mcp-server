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


# ---------------------------------------------------------------------------
# Loan formatters (Plan 03)
# ---------------------------------------------------------------------------


def format_loan_list(
    loans: list[dict], borrower_balances: dict | None = None
) -> str:
    """Format loans for display with optional balance info.

    Args:
        loans: List of loan dicts from API.
        borrower_balances: Optional mapping of borrower_id -> balance dict
            from /api/reports/borrowers.
    """
    if not loans:
        return "No loans found."

    lines = [f"Loans ({len(loans)}):"]
    lines.append("")
    for i, loan in enumerate(loans, 1):
        lid = str(loan.get("id", ""))[:8]
        principal = loan.get("principal", 0)
        date = loan.get("loan_date", "")
        status = loan.get("status", "")
        charge_day = loan.get("interest_charge_day", "")
        borrower_id = loan.get("borrower_id", "")
        borrower_name = loan.get("borrower_name", "")

        header = f"  {i}. Loan {lid}"
        if borrower_name:
            header += f"  ({borrower_name})"
        lines.append(header)
        lines.append(
            f"     Principal: {format_money(principal)} | "
            f"Date: {date} | Status: {status}"
        )
        lines.append(f"     Interest charge day: {charge_day}")

        if borrower_balances and borrower_id in borrower_balances:
            bal = borrower_balances[borrower_id]
            remaining = bal.get("remaining_balance", 0)
            lines.append(
                f"     Borrower remaining balance: {format_money(remaining)}"
            )
        lines.append("")

    return "\n".join(lines).rstrip()


def format_loan_detail(loan: dict, balance_info: dict | None = None) -> str:
    """Format single loan detail with optional balance info."""
    lid = str(loan.get("id", ""))[:8]
    full_id = loan.get("id", "")
    borrower_id = loan.get("borrower_id", "")
    principal = loan.get("principal", 0)
    date = loan.get("loan_date", "")
    status = loan.get("status", "")
    charge_day = loan.get("interest_charge_day", "")

    lines = [f"Loan Detail: {lid}"]
    lines.append(f"  Full ID: {full_id}")
    lines.append(f"  Borrower ID: {borrower_id}")
    lines.append(f"  Principal: {format_money(principal)}")
    lines.append(f"  Loan date: {date}")
    lines.append(f"  Status: {status}")
    lines.append(f"  Interest charge day: {charge_day}")

    if balance_info:
        remaining = balance_info.get("remaining_balance", 0)
        paid = balance_info.get("total_paid", 0)
        lines.append("")
        lines.append("  Balance (borrower-level):")
        lines.append(f"    Remaining: {format_money(remaining)}")
        lines.append(f"    Total paid: {format_money(paid)}")
        active_count = balance_info.get("active_loan_count", 0)
        if active_count > 1:
            lines.append(
                f"    Note: Borrower has {active_count} active loans; "
                f"balance is borrower-level total, not per-loan."
            )

    # Funding sources
    sources = loan.get("funding_sources", [])
    if sources:
        lines.append("")
        lines.append("  Funding sources:")
        for src in sources:
            stype = src.get("source_type", "")
            amt = src.get("amount", 0)
            funder = src.get("external_funder_name", "")
            desc = f"    - {stype}: {format_money(amt)}"
            if funder:
                desc += f" ({funder})"
            lines.append(desc)

    # Renewal chain
    chain = loan.get("renewal_chain", [])
    if chain:
        lines.append("")
        lines.append(f"  Renewal chain ({len(chain)} loans):")
        for entry in chain:
            cid = str(entry.get("id", ""))[:8]
            cprincipal = entry.get("principal", 0)
            cdate = entry.get("loan_date", "")
            cstatus = entry.get("status", "")
            lines.append(
                f"    - {cid} | {format_money(cprincipal)} | "
                f"{cdate} | {cstatus}"
            )

    return "\n".join(lines)


def format_loan_created(loan: dict) -> str:
    """Confirmation after creating a loan."""
    lid = str(loan.get("id", ""))[:8]
    full_id = loan.get("id", "")
    borrower_id = loan.get("borrower_id", "")
    principal = loan.get("principal", 0)
    date = loan.get("loan_date", "")

    lines = ["Loan created successfully:"]
    lines.append(f"  Loan ID: {lid} (full: {full_id})")
    lines.append(f"  Borrower ID: {borrower_id}")
    lines.append(f"  Principal: {format_money(principal)}")
    lines.append(f"  Loan date: {date}")

    sources = loan.get("funding_sources", [])
    if sources:
        lines.append("  Funding:")
        for src in sources:
            stype = src.get("source_type", "")
            amt = src.get("amount", 0)
            funder = src.get("external_funder_name", "")
            desc = f"    - {stype}: {format_money(amt)}"
            if funder:
                desc += f" ({funder})"
            lines.append(desc)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Payment formatters (Plan 03)
# ---------------------------------------------------------------------------


def format_payment_response(payment: dict) -> str:
    """Format payment confirmation with allocations."""
    pid = str(payment.get("id", ""))[:8]
    full_id = payment.get("id", "")
    date = payment.get("payment_date", "")
    total = payment.get("total_amount", 0)
    notes = payment.get("notes", "")

    lines = ["Payment recorded successfully:"]
    lines.append(f"  Payment ID: {pid} (full: {full_id})")
    lines.append(f"  Date: {date}")
    lines.append(f"  Total amount: {format_money(total)}")
    if notes:
        lines.append(f"  Notes: {notes}")

    allocations = payment.get("allocations", [])
    if allocations:
        lines.append("")
        lines.append(f"  Allocations ({len(allocations)}):")
        for alloc in allocations:
            loan_id = str(alloc.get("loan_id", ""))[:8]
            amount = alloc.get("amount", 0)
            lines.append(f"    - Loan {loan_id}: {format_money(amount)}")

    return "\n".join(lines)


def format_loan_balance(loan: dict, balance: dict) -> str:
    """Format balance check for a specific loan."""
    lid = str(loan.get("id", ""))[:8]
    full_id = loan.get("id", "")
    status = loan.get("status", "")
    principal = loan.get("principal", 0)
    charge_day = loan.get("interest_charge_day", "")

    remaining = balance.get("remaining_balance", 0)
    paid = balance.get("total_paid", 0)
    borrower_name = balance.get("borrower_name", "")
    active_count = balance.get("active_loan_count", 0)

    lines = [f"Loan Balance: {lid}"]
    lines.append(f"  Full ID: {full_id}")
    if borrower_name:
        lines.append(f"  Borrower: {borrower_name}")
    lines.append(f"  Status: {status}")
    lines.append(f"  Principal: {format_money(principal)}")
    lines.append(f"  Remaining balance: {format_money(remaining)}")
    lines.append(f"  Total paid: {format_money(paid)}")
    lines.append(f"  Interest charge day: {charge_day}")

    if active_count > 1:
        lines.append("")
        lines.append(
            f"  Note: Borrower has {active_count} active loans. "
            f"The remaining balance ({format_money(remaining)}) is the "
            f"borrower-level total across all active loans, not just this loan."
        )

    # Funding sources from loan detail
    sources = loan.get("funding_sources", [])
    if sources:
        lines.append("")
        lines.append("  Funding sources:")
        for src in sources:
            stype = src.get("source_type", "")
            amt = src.get("amount", 0)
            funder = src.get("external_funder_name", "")
            desc = f"    - {stype}: {format_money(amt)}"
            if funder:
                desc += f" ({funder})"
            lines.append(desc)

    # Renewal chain from loan detail
    chain = loan.get("renewal_chain", [])
    if chain:
        lines.append("")
        lines.append(f"  Renewal chain ({len(chain)} loans):")
        for entry in chain:
            cid = str(entry.get("id", ""))[:8]
            cprincipal = entry.get("principal", 0)
            cdate = entry.get("loan_date", "")
            cstatus = entry.get("status", "")
            lines.append(
                f"    - {cid} | {format_money(cprincipal)} | "
                f"{cdate} | {cstatus}"
            )

    return "\n".join(lines)
