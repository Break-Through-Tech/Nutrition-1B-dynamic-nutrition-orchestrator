"""Configuration and secret loading (Task 6 infrastructure).

The USDA API key must never be committed. This module makes the supported
alternative frictionless: put the key in a local `.env` file that git ignores,
and every script picks it up automatically.

Resolution order, first hit wins:

  1. An already-set `USDA_API_KEY` environment variable (CI, or a shell export)
  2. A `.env` file at the repository root

`load_dotenv()` writes into `os.environ`, so Task 1's `USDAClient` — which
reads `os.getenv("USDA_API_KEY")` — works unchanged with no edits to
`API_File.py`.

Deliberately dependency-free. The `.env` format is simple enough that parsing
it here is clearer for the team than adding a package, and it keeps
`requirements.txt` honest.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = REPO_ROOT / ".env"

API_KEY_VAR = "USDA_API_KEY"

SIGNUP_URL = "https://fdc.nal.usda.gov/api-key-signup"


class MissingAPIKeyError(RuntimeError):
    """Raised with setup instructions rather than a bare KeyError."""


def parse_env_text(text: str) -> dict[str, str]:
    """Parse `.env` content into a dict.

    Supports `KEY=value`, `export KEY=value`, `#` comments, blank lines, and
    optional surrounding single or double quotes.
    """
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        # Strip one matching pair of surrounding quotes, if present.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        if key:
            values[key] = value
    return values


def load_dotenv(path: str | Path | None = None, override: bool = False) -> dict[str, str]:
    """Load a `.env` file into `os.environ`. Missing file is not an error.

    Returns the values that were applied, so callers can report what was found
    without printing the secret itself.
    """
    env_path = Path(path) if path else DEFAULT_ENV_PATH
    if not env_path.exists():
        return {}

    values = parse_env_text(env_path.read_text(encoding="utf-8"))
    applied: dict[str, str] = {}
    for key, value in values.items():
        # An explicitly exported variable wins unless override is requested,
        # so CI settings are not silently replaced by a stale local file.
        if override or not os.environ.get(key):
            os.environ[key] = value
            applied[key] = value
    return applied


def get_api_key(required: bool = True) -> str | None:
    """Return the USDA API key, loading `.env` first if needed."""
    load_dotenv()
    key = os.environ.get(API_KEY_VAR, "").strip()

    if key:
        return key
    if not required:
        return None

    raise MissingAPIKeyError(
        f"No {API_KEY_VAR} found.\n"
        f"\n"
        f"  1. Get a free key (instant): {SIGNUP_URL}\n"
        f"  2. Copy .env.example to .env\n"
        f"  3. Put your key in it:  {API_KEY_VAR}=your_key_here\n"
        f"\n"
        f".env is git-ignored, so the key stays off the public repository."
    )


def mask(secret: str) -> str:
    """Render a key safely for logs: first 4 and last 4 characters only."""
    if not secret:
        return "(empty)"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"


__all__ = [
    "API_KEY_VAR",
    "DEFAULT_ENV_PATH",
    "MissingAPIKeyError",
    "SIGNUP_URL",
    "get_api_key",
    "load_dotenv",
    "mask",
    "parse_env_text",
]
