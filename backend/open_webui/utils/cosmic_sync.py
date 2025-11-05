"""Utilities to trigger CoSMIC database synchronization via webhook.

This module posts a small JSON payload to the CoSMIC backend endpoint
exposed by the CoSMIC service to request an immediate sync of data from
OpenWebUI DB into the CoSMIC DB.

Endpoint (served by CoSMIC): POST /webhook/openwebui/sync
Payload: {"type": "users" | "llms" | "all"}
Header (optional): X-Cosmic-Webhook-Secret: <token>

The base URL is resolved in this order:
- OPENSI_COSMIC_API_BASE_URL env var (e.g., http://cosmic:3000)
- fallback to http://cosmic:3000 (Docker network service name)
"""

from __future__ import annotations

import logging
import os
from typing import Literal

import requests
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("WEBHOOK", logging.INFO))


def _get_cosmic_base_url() -> str:
    base = os.environ.get("OPENSI_COSMIC_API_BASE_URL")
    if base and base.strip():
        base = base.rstrip("/")
        # If someone set localhost/127.0.0.1 inside the container, prefer service name
        if "localhost" in base or "127.0.0.1" in base:
            return "http://cosmic:3000"
        return base
    # Default to the Docker service name reachable from the same network
    return "http://cosmic:3000"


def trigger_cosmic_sync(kind: Literal["users", "llms", "all"]) -> None:
    """Trigger immediate synchronization in CoSMIC.

    Errors are logged but never raised to avoid blocking user actions in
    OpenWebUI. This function is intended to be best-effort.
    """
    url = f"{_get_cosmic_base_url()}/webhook/openwebui/sync"
    headers = {}
    secret = os.environ.get("COSMIC_WEBHOOK_SECRET")
    if secret:
        headers["X-Cosmic-Webhook-Secret"] = secret

    payload = {"type": kind}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        resp.raise_for_status()
        log.debug("trigger_cosmic_sync(%s): %s", kind, resp.text)
    except Exception as e:
        # Log at debug to avoid noisy logs in normal operation
        log.debug("trigger_cosmic_sync error: %s", e)
