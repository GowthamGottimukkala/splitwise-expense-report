"""Barebone Splitwise API helpers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import requests


BASE_URL = "https://secure.splitwise.com/api/v3.0"
DEFAULT_TIMEOUT_SECONDS = 15


def api_get(
    token: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    base_url: str = BASE_URL,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """Send a GET request to the Splitwise API and return the JSON payload."""

    url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()


def get_current_user(token: str) -> Dict[str, Any]:
    """Return the current authenticated user payload."""

    payload = api_get(token, "/get_current_user")
    return payload["user"]


def get_expenses(
    token: str,
    group_id: Optional[int] = None,
    dated_after: Optional[str] = None,
    dated_before: Optional[str] = None,
    page_size: int = 200,
) -> List[Dict[str, Any]]:
    """Return all expenses matching the provided filters."""

    expenses: List[Dict[str, Any]] = []
    offset = 0

    while True:
        params: Dict[str, Any] = {"limit": page_size, "offset": offset}
        if group_id is not None:
            params["group_id"] = group_id
        if dated_after:
            params["dated_after"] = dated_after
        if dated_before:
            params["dated_before"] = dated_before

        payload = api_get(token, "/get_expenses", params=params)
        batch = payload.get("expenses", [])
        expenses.extend(batch)

        if len(batch) < page_size:
            break
        offset += page_size

    return expenses


def iter_user_shares(expense: Dict[str, Any], user_id: int) -> Iterable[str]:
    """Yield the owed share string values for the given user in an expense."""

    for user_entry in expense.get("users", []):
        user_obj = user_entry.get("user", {})
        if int(user_obj.get("id", -1)) == user_id:
            yield user_entry.get("owed_share", "0")


def user_paid_share(expense: Dict[str, Any], user_id: int) -> str:
    """Return the paid share string for the given user in an expense."""

    for user_entry in expense.get("users", []):
        user_obj = user_entry.get("user", {})
        if int(user_obj.get("id", -1)) == user_id:
            return user_entry.get("paid_share", "0")
    return "0"