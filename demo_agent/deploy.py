#!/usr/bin/env python3
"""
deploy.py — Deploy the ADK 2.0 Report Generation agent to Vertex AI Agent Engine.

Usage:
    # Create a new Agent Engine instance
    python deploy.py

    # Update an existing Agent Engine instance
    python deploy.py --agent-engine-id <RESOURCE_ID>

    # Override project / region
    python deploy.py --project my-project --region us-central1

    # Dry-run (stage files only, do not deploy)
    python deploy.py --dry-run

Prerequisites:
    1. gcloud CLI authenticated:    gcloud auth login
    2. ADC for Python SDK:          gcloud auth application-default login
    3. Vertex AI API enabled:       gcloud services enable aiplatform.googleapis.com
    4. .env in src/ with GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION
"""

from __future__ import annotations

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_FOLDER = os.path.join(SCRIPT_DIR, "src")           # the ADK agent root
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")               # project-level .env


def _load_env_defaults() -> dict[str, str]:
    """Read key=value pairs from .env (ignoring comments and blanks)."""
    defaults: dict[str, str] = {}
    if not os.path.exists(ENV_FILE):
        return defaults
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            defaults[key.strip()] = value.strip()
    return defaults


def parse_args() -> argparse.Namespace:
    env = _load_env_defaults()
    parser = argparse.ArgumentParser(
        description="Deploy ADK agent to Vertex AI Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project",
        default=env.get("GOOGLE_CLOUD_PROJECT"),
        help="GCP project ID  (default: from .env GOOGLE_CLOUD_PROJECT)",
    )
    parser.add_argument(
        "--region",
        default=env.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        help="GCP region       (default: from .env GOOGLE_CLOUD_LOCATION)",
    )
    parser.add_argument(
        "--display-name",
        default="report-generation-workflow",
        help="Display name shown in the Cloud Console",
    )
    parser.add_argument(
        "--description",
        default="ADK 2.0 graph workflow: intent routing → web search → report → markdown table",
        help="Description for the Agent Engine resource",
    )
    parser.add_argument(
        "--agent-engine-id",
        default=None,
        help="Existing Agent Engine resource ID to update (omit to create new)",
    )
    parser.add_argument(
        "--trace-to-cloud",
        action="store_true",
        default=True,
        help="Enable Cloud Trace for the deployed agent",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Stage files and validate but do NOT deploy",
    )
    return parser.parse_args()


def preflight_checks(project: str | None, region: str | None) -> None:
    """Validate the environment before attempting deployment."""
    errors: list[str] = []

    if not project:
        errors.append(
            "No GCP project. Set GOOGLE_CLOUD_PROJECT in .env or pass --project."
        )
    if not region:
        errors.append(
            "No GCP region. Set GOOGLE_CLOUD_LOCATION in .env or pass --region."
        )

    agent_py = os.path.join(AGENT_FOLDER, "agent.py")
    if not os.path.isfile(agent_py):
        errors.append(f"agent.py not found at {agent_py}")

    req_txt = os.path.join(AGENT_FOLDER, "requirements.txt")
    if not os.path.isfile(req_txt):
        errors.append(
            f"requirements.txt not found at {req_txt}. "
            "Agent Engine needs this to install dependencies on the server."
        )

    if errors:
        print("❌  Preflight failed:\n")
        for err in errors:
            print(f"   • {err}")
        sys.exit(1)

    print(f"✅  Project:  {project}")
    print(f"✅  Region:   {region}")
    print(f"✅  Agent:    {AGENT_FOLDER}")


def deploy(args: argparse.Namespace) -> None:
    """Run the deployment via the ADK CLI deploy module."""
    from google.adk.cli.cli_deploy import to_agent_engine

    print("\n" + "=" * 60)
    print("  Deploying to Vertex AI Agent Engine")
    print("=" * 60 + "\n")

    to_agent_engine(
        agent_folder=AGENT_FOLDER,
        adk_app="app",                           # generated entrypoint filename
        project=args.project,
        region=args.region,
        display_name=args.display_name,
        description=args.description,
        agent_engine_id=args.agent_engine_id,     # None → create new
        trace_to_cloud=args.trace_to_cloud,
        env_file=ENV_FILE,
        adk_app_object="root_agent",              # matches src/agent.py
        skip_agent_import_validation=True,        # avoids local import issues
    )


def main() -> None:
    args = parse_args()

    print("\n🚀  ADK Agent Engine Deployment\n")
    preflight_checks(args.project, args.region)

    if args.dry_run:
        print("\n🔍  Dry-run complete — skipping actual deployment.")
        return

    deploy(args)
    print("\n✅  Deployment complete.\n")


if __name__ == "__main__":
    main()
