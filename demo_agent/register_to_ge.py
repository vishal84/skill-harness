"""
register_to_ge.py — Register a deployed Agent Engine instance to Gemini Enterprise.

Reads AGENT_ENGINE_ID and GEMINI_ENTERPRISE_APP_ID from .env, resolves the
project number automatically, and calls the Discovery Engine API to register
the agent.  No AUTH_ID / authorization_config is used.

Usage:
    uv run python register_to_ge.py

Prerequisites:
    1. gcloud auth application-default login
    2. A successful deploy.py run (AGENT_ENGINE_ID saved in .env)
"""

import os
import sys
import logging
import json
import subprocess

import requests as http_requests          # avoid shadowing google.auth.transport.requests
import google.auth
import google.auth.transport.requests
from dotenv import load_dotenv, dotenv_values


def _get_project_number(project_id: str, logger: logging.Logger) -> str | None:
    """Resolve the numeric project number from the project ID via gcloud."""
    try:
        result = subprocess.run(
            [
                "gcloud", "projects", "describe", project_id,
                "--format=value(projectNumber)",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        number = result.stdout.strip()
        logger.info("Resolved project number: %s", number)
        return number
    except Exception as exc:
        logger.error("Failed to resolve project number via gcloud: %s", exc)
        return None


def main():
    """Register a deployed Agent Engine instance to a Gemini Enterprise App."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    # ── Load .env ────────────────────────────────────────────────────────
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    load_dotenv(dotenv_path=env_path)
    env_vars = dotenv_values(dotenv_path=env_path)

    AGENT_ENGINE_ID = env_vars.get("AGENT_ENGINE_ID")
    GEMINI_ENTERPRISE_APP_ID = env_vars.get("GEMINI_ENTERPRISE_APP_ID")
    GOOGLE_CLOUD_PROJECT = env_vars.get("GOOGLE_CLOUD_PROJECT")

    # Validate
    missing = []
    if not AGENT_ENGINE_ID:
        missing.append("AGENT_ENGINE_ID")
    if not GEMINI_ENTERPRISE_APP_ID:
        missing.append("GEMINI_ENTERPRISE_APP_ID")
    if not GOOGLE_CLOUD_PROJECT:
        missing.append("GOOGLE_CLOUD_PROJECT")

    if missing:
        logger.error("Missing required .env variables: %s", ", ".join(missing))
        logger.error("Run deploy.py first to populate AGENT_ENGINE_ID.")
        sys.exit(1)

    # Resolve project number (the Discovery Engine API requires it)
    PROJECT_NUMBER = env_vars.get("GOOGLE_CLOUD_PROJECT_NUMBER") or _get_project_number(
        GOOGLE_CLOUD_PROJECT, logger
    )
    if not PROJECT_NUMBER:
        logger.error(
            "Could not determine project number. "
            "Set GOOGLE_CLOUD_PROJECT_NUMBER in .env or ensure gcloud is configured."
        )
        sys.exit(1)

    logger.info("Agent Engine ID : %s", AGENT_ENGINE_ID)
    logger.info("GE App ID       : %s", GEMINI_ENTERPRISE_APP_ID)
    logger.info("Project Number  : %s", PROJECT_NUMBER)

    # ── Agent metadata ───────────────────────────────────────────────────
    AGENT_DISPLAY_NAME = "Report Generation Workflow"
    AGENT_DESCRIPTION = (
        "ADK 2.0 graph workflow: intent routing → web search → "
        "report generation → markdown table"
    )

    # ── Authenticate ─────────────────────────────────────────────────────
    try:
        credentials, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        access_token = credentials.token
    except google.auth.exceptions.DefaultCredentialsError:
        logger.error(
            "Authentication failed.  Run:  gcloud auth application-default login"
        )
        sys.exit(1)

    # ── Build API request ────────────────────────────────────────────────
    api_url = (
        f"https://discoveryengine.googleapis.com/v1alpha/"
        f"projects/{PROJECT_NUMBER}/locations/global/"
        f"collections/default_collection/engines/{GEMINI_ENTERPRISE_APP_ID}/"
        f"assistants/default_assistant/agents"
    )

    payload = {
        "displayName": AGENT_DISPLAY_NAME,
        "description": AGENT_DESCRIPTION,
        "adk_agent_definition": {
            "tool_settings": {
                "tool_description": AGENT_DESCRIPTION,
            },
            "provisioned_reasoning_engine": {
                "reasoning_engine": AGENT_ENGINE_ID,
            },
        },
        # No authorization_config — not needed for this agent
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-goog-user-project": PROJECT_NUMBER,
    }

    logger.info("Calling Discovery Engine API…")
    logger.debug("URL: %s", api_url)
    logger.debug("Payload: %s", json.dumps(payload, indent=2))

    # ── Call the API ─────────────────────────────────────────────────────
    try:
        response = http_requests.post(
            api_url,
            headers=headers,
            data=json.dumps(payload),
        )
        response.raise_for_status()

        logger.info("✅ Successfully registered agent to Gemini Enterprise!")
        logger.info("Response: %s", json.dumps(response.json(), indent=2))

    except http_requests.exceptions.HTTPError as exc:
        logger.error("HTTP error during registration: %s", exc)
        logger.error("Response body: %s", exc.response.text)
        sys.exit(1)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
