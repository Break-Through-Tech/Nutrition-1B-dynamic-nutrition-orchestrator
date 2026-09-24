"""Verify the USDA API key is present and actually works (Task 6 setup).

Run this before any capture. It makes exactly one cheap request, so a bad key
is caught in a second rather than partway through a 52-query run.

    python scripts/check_api_key.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nutrition_engine.config import (  # noqa: E402
    API_KEY_VAR,
    DEFAULT_ENV_PATH,
    MissingAPIKeyError,
    SIGNUP_URL,
    get_api_key,
    mask,
)

FDC_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


def main() -> int:
    print("USDA API key check")
    print("-" * 46)
    print(f".env location : {DEFAULT_ENV_PATH}")
    print(f".env present  : {'yes' if DEFAULT_ENV_PATH.exists() else 'no'}")

    try:
        key = get_api_key()
    except MissingAPIKeyError as error:
        print(f"{API_KEY_VAR}      : NOT FOUND\n")
        print(error)
        return 1

    print(f"{API_KEY_VAR}      : found ({mask(key)})")

    if key == "your_key_here":
        print("\nThat is the placeholder from .env.example.")
        print(f"Replace it with a real key: {SIGNUP_URL}")
        return 1

    try:
        import httpx
    except ImportError:
        print("\nhttpx is not installed. Run: pip install -r requirements.txt")
        return 1

    print("\nCalling USDA with one test query ('paneer')...")
    try:
        response = httpx.get(
            FDC_SEARCH_URL,
            params={"api_key": key, "query": "paneer", "pageSize": 1},
            timeout=15.0,
        )
    except Exception as error:  # network-level failure, not an API rejection
        print(f"Network error: {type(error).__name__}: {error}")
        return 1

    if response.status_code == 200:
        payload = response.json()
        hits = payload.get("totalHits", 0)
        print(f"OK  HTTP 200 - {hits} results for 'paneer'")
        print("\nKey works. Next:")
        print("  python scripts/snapshot_usda_candidates.py --validation")
        return 0

    # USDA returns 403 for a bad key and 429 once the hourly quota is spent.
    if response.status_code == 403:
        print("FAIL  HTTP 403 - the key was rejected.")
        print(f"      Check for typos or request a new key: {SIGNUP_URL}")
    elif response.status_code == 429:
        print("FAIL  HTTP 429 - rate limit reached.")
        print("      A personal key allows 1,000/hour; DEMO_KEY only 30.")
        print("      Wait an hour, or use your own key.")
    else:
        print(f"FAIL  HTTP {response.status_code}")
        print(f"      {response.text[:200]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
