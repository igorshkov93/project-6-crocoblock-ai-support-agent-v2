"""Thin client for the WordPress REST API."""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("WP_BASE_URL", "").rstrip("/")
USER = os.getenv("WP_USER", "")
APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

TIMEOUT = 15


class WPError(Exception):
    """Raised when the WordPress API returns an error."""


def _auth_header() -> str:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return f"Basic {token}"


def wp_get(path: str, params: dict | None = None) -> dict | list:
    """Send a GET request to a WP REST endpoint and return parsed JSON.

    Args:
        path: Endpoint path after /wp-json, e.g. "wp/v2/users/me".
        params: Optional query parameters.
    """
    if not all([BASE_URL, USER, APP_PASSWORD]):
        raise WPError("WordPress credentials are missing from .env")

    url = f"{BASE_URL}/wp-json/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    request = urllib.request.Request(
        url, headers={"Authorization": _auth_header()}
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        body = error.read().decode()[:200]
        raise WPError(f"HTTP {error.code} on {path}: {body}") from error
    except urllib.error.URLError as error:
        raise WPError(f"Cannot reach {BASE_URL}: {error.reason}") from error