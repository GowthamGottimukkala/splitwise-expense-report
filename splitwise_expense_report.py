"""Splitwise expense report entrypoint."""

from __future__ import annotations

import argparse
import os
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple

from splitwise_api_client import get_current_user, get_expenses, iter_user_shares, user_paid_share


SummaryRow = Tuple[str, Decimal, Decimal]
CategoryRow = Tuple[str, str, Decimal]


def _as_decimal(value: str) -> Decimal:
    """Convert a string amount to a Decimal for accurate sums."""

    return Decimal(value or "0")


def _current_month_range(today: date | None = None) -> Tuple[str, str]:
    """Return date range strings for the current calendar month."""

    today = today or date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    month_end = next_month - date.resolution
    return month_start.isoformat(), month_end.isoformat()


def _expense_currency(expense: Dict[str, object], fallback: str) -> str:
    """Return the currency code for an expense or a fallback value."""

    currency = expense.get("currency_code") if isinstance(expense, dict) else None
    return currency or fallback


def _expense_category(expense: Dict[str, object]) -> str:
    """Return the category name for an expense."""

    category = expense.get("category", {}) if isinstance(expense, dict) else {}
    if isinstance(category, dict):
        return category.get("name", "Uncategorized")
    return "Uncategorized"


def aggregate_summary(expenses: Iterable[Dict[str, object]], user_id: int, default_currency: str) -> List[SummaryRow]:
    """Aggregate totals for my share and what I paid by currency."""

    total_share: Dict[str, Decimal] = defaultdict(Decimal)
    total_paid: Dict[str, Decimal] = defaultdict(Decimal)

    for expense in expenses:
        if bool(expense.get("payment")):
            continue
        currency = _expense_currency(expense, default_currency)
        for share in iter_user_shares(expense, user_id):
            total_share[currency] += _as_decimal(share)
        total_paid[currency] += _as_decimal(user_paid_share(expense, user_id))

    rows: List[SummaryRow] = []
    for currency in sorted(set(total_share) | set(total_paid)):
        rows.append((currency, total_share[currency], total_paid[currency]))
    return rows


def aggregate_categories(
    expenses: Iterable[Dict[str, object]],
    user_id: int,
    default_currency: str,
) -> List[CategoryRow]:
    """Aggregate user owed shares per category and currency from Splitwise expenses."""

    totals: Dict[Tuple[str, str], Decimal] = defaultdict(Decimal)

    for expense in expenses:
        if bool(expense.get("payment")):
            continue
        currency = _expense_currency(expense, default_currency)
        category_name = _expense_category(expense)

        for share in iter_user_shares(expense, user_id):
            totals[(currency, category_name)] += _as_decimal(share)

    rows = [(currency, category, amount) for (currency, category), amount in totals.items()]
    rows.sort(key=lambda row: (row[0], -row[2], row[1]))
    return rows


def render_summary(rows: Iterable[SummaryRow]) -> str:
    """Render the high-level summary table for my share vs paid."""

    formatted = [(currency, f"{share:.2f}", f"{paid:.2f}") for currency, share, paid in rows]
    if not formatted:
        return "No expenses found for the selected criteria."

    headers = ("Currency", "My total share", "Total I paid")
    widths = [len(header) for header in headers]
    for row in formatted:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    header_line = "  ".join(headers[index].ljust(widths[index]) for index in range(len(headers)))
    divider = "  ".join("-" * width for width in widths)
    body = "\n".join(
        "  ".join(row[index].ljust(widths[index]) for index in range(len(headers))) for row in formatted
    )
    return f"{header_line}\n{divider}\n{body}"


def render_categories(rows: Iterable[CategoryRow]) -> str:
    """Render the category totals table by currency and share."""

    formatted = [(currency, category, f"{amount:.2f}") for currency, category, amount in rows]
    if not formatted:
        return "No expenses found for the selected criteria."

    headers = ("Currency", "Category", "My share")
    widths = [len(header) for header in headers]
    for row in formatted:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    header_line = "  ".join(headers[index].ljust(widths[index]) for index in range(len(headers)))
    divider = "  ".join("-" * width for width in widths)
    body = "\n".join(
        "  ".join(row[index].ljust(widths[index]) for index in range(len(headers))) for row in formatted
    )
    return f"{header_line}\n{divider}\n{body}"


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for CLI inputs."""

    parser = argparse.ArgumentParser(description="Splitwise expense summary by category.")
    parser.add_argument("--token", default=os.getenv("SPLITWISE_TOKEN"), help="Splitwise API bearer token.")
    parser.add_argument("--group-id", type=int, help="Only include expenses from a specific group.")
    parser.add_argument(
        "--dated-after",
        default=None,
        help="Only include expenses after this date (YYYY-MM-DD). Defaults to current month.",
    )
    parser.add_argument(
        "--dated-before",
        default=None,
        help="Only include expenses before this date (YYYY-MM-DD). Defaults to current month.",
    )
    parser.add_argument("--currency", default="USD", help="Currency label to display in output.")
    return parser


def run(argv: List[str] | None = None) -> int:
    """Run the Splitwise expense report and print the results."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.token:
        parser.error("Provide --token or set SPLITWISE_TOKEN.")

    dated_after = args.dated_after
    dated_before = args.dated_before
    if not dated_after and not dated_before:
        dated_after, dated_before = _current_month_range()

    user = get_current_user(args.token)
    expenses = get_expenses(
        args.token,
        group_id=args.group_id,
        dated_after=dated_after,
        dated_before=dated_before,
    )

    user_id = int(user["id"])
    summary_rows = aggregate_summary(expenses, user_id, args.currency)
    category_rows = aggregate_categories(expenses, user_id, args.currency)

    print(f"Date range: {dated_after}  →  {dated_before}\n")
    print("SUMMARY (non-payment expenses only)")
    print(render_summary(summary_rows))
    print("\nCATEGORY TOTALS (by my share)")
    print(render_categories(category_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())