"""Optional Streamlit adapter for the local API health and scope shell."""

from __future__ import annotations

import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


def _health_url(api_url: str) -> str:
    """Build the public liveness URL without accepting a path override."""
    return f"{api_url.rstrip('/')}/api/v1/health/live"


def fetch_api_health(api_url: str, *, timeout: float = 3.0) -> tuple[bool, dict[str, Any]]:
    """Read the API liveness contract without authenticating or mutating state."""
    request = Request(_health_url(api_url), method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            import json

            value = json.loads(payload)
            if not isinstance(value, dict):
                return False, {"status": "invalid_response", "detail": "API liveness response is not an object"}
            return response.status == 200, value
    except (OSError, URLError, ValueError) as exc:
        return False, {"status": "unreachable", "detail": str(exc)}


def main() -> None:
    """Render the optional local UI shell without duplicating orchestrator logic."""
    import streamlit as st

    api_url = os.environ.get("AUTONET_API_URL", "http://127.0.0.1:8000")
    st.set_page_config(page_title="AutoNetArchitect", page_icon=None, layout="wide")
    st.title("AutoNetArchitect")
    st.caption("V1 local-single-user supervised engineering control plane")

    healthy, payload = fetch_api_health(api_url)
    if healthy:
        st.success("API liveness is available")
    else:
        st.warning("API liveness is not currently available")
    st.json({"api_url": api_url, "liveness": payload, "read_only": True, "scope": "local-single-user"})
    st.info("Workflow actions remain governed by the API, orchestrators, approvals, audit, backup, verification, and rollback controls.")


if __name__ == "__main__":
    main()
