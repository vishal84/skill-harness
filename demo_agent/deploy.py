"""
deploy.py — Deploy the ADK 2.0 Report Generation agent to Vertex AI Agent Engine.

Uses the same pattern as the knowledge-graph-agent deploy script:
  AdkApp + vertexai.Client + agent_engines.create/update

Usage:
    # Create a new Agent Engine instance
    python deploy.py

    # Update an existing Agent Engine instance (set AGENT_ENGINE_ID in .env)
    python deploy.py

Prerequisites:
    1. gcloud auth application-default login
    2. Vertex AI API enabled on the project
    3. A GCS staging bucket (set STAGING_BUCKET in .env)
"""

import os
import sys
import logging
from datetime import datetime

import vertexai
from vertexai.agent_engines import AdkApp
from dotenv import load_dotenv, dotenv_values, set_key

# ---------------------------------------------------------------------------
# Ensure local src/ is importable so we can reference root_agent
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "src")
sys.path.insert(0, SRC_DIR)

from agents.report_workflow import create_report_workflow  # noqa: E402


# ---------------------------------------------------------------------------
# Config builder
# ---------------------------------------------------------------------------
def _build_agent_engine_config(
    *,
    gcs_dir_name: str,
    staging_bucket: str,
    google_cloud_location: str,
):
    return dict(
        agent_framework="google-adk",
        display_name="Report Generation Workflow",
        description="ADK 2.0 graph workflow: intent routing → web search → report → markdown table",
        staging_bucket=staging_bucket,
        gcs_dir_name=gcs_dir_name,
        extra_packages=["./src"],
        requirements=[
            "google-adk>=2.0.0b1",
            "google-cloud-aiplatform[adk,agent_engines]",
            "markdown>=3.4.0",
        ],
        env_vars={
            "GOOGLE_CLOUD_LOCATION": google_cloud_location,
            "GOOGLE_GENAI_USE_VERTEXAI": "1",
        },
    )


# ---------------------------------------------------------------------------
# Resolve existing engine (update vs create)
# ---------------------------------------------------------------------------
def _resolve_existing_agent_engine(client, agent_engine_id, logger):
    if not agent_engine_id:
        return None

    if "/reasoningEngines/" not in agent_engine_id:
        logger.warning(
            "AGENT_ENGINE_ID is set but is not a valid resource name: %s",
            agent_engine_id,
        )
        return None

    try:
        client.agent_engines.get(name=agent_engine_id)
        logger.info("Found existing Agent Engine: %s", agent_engine_id)
        return agent_engine_id
    except Exception as exc:
        logger.warning(
            "AGENT_ENGINE_ID set but not fetchable — will create new. id=%s error=%s",
            agent_engine_id,
            exc,
        )
        return None


# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------
def deploy():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Load .env
    env_path = os.path.join(SCRIPT_DIR, ".env")
    load_dotenv(dotenv_path=env_path)
    env_vars = dotenv_values(dotenv_path=env_path)

    GOOGLE_CLOUD_PROJECT = env_vars.get("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION = env_vars.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    STAGING_BUCKET = env_vars.get("STAGING_BUCKET")
    AGENT_ENGINE_ID = env_vars.get("AGENT_ENGINE_ID")

    if not GOOGLE_CLOUD_PROJECT:
        logger.error("GOOGLE_CLOUD_PROJECT not set in .env")
        sys.exit(1)
    if not STAGING_BUCKET:
        logger.error("STAGING_BUCKET not set in .env  (e.g. gs://my-bucket)")
        sys.exit(1)

    gcs_dir_name = f"report-agent-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    # Build the ADK app from our root_agent
    root_agent = create_report_workflow()
    deployment_app = AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    logger.info(
        "Initializing Vertex AI — project=%s  location=%s  bucket=%s",
        GOOGLE_CLOUD_PROJECT,
        GOOGLE_CLOUD_LOCATION,
        STAGING_BUCKET,
    )

    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    client = vertexai.Client(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )

    config = _build_agent_engine_config(
        gcs_dir_name=gcs_dir_name,
        staging_bucket=STAGING_BUCKET,
        google_cloud_location=GOOGLE_CLOUD_LOCATION,
    )

    existing = _resolve_existing_agent_engine(client, AGENT_ENGINE_ID, logger)

    if existing:
        logger.info("Updating existing Agent Engine: %s", existing)
        remote_app = client.agent_engines.update(
            name=existing,
            agent=deployment_app,
            config=config,
        )
    else:
        logger.info("Creating new Agent Engine deployment")
        remote_app = client.agent_engines.create(
            agent=deployment_app,
            config=config,
        )

    engine_id = remote_app.api_resource.name
    logger.info("✅ Deployed successfully — resource: %s", engine_id)
    print(f"\nAgent Engine ID: {engine_id}")

    # Persist the engine ID back to .env for future updates
    try:
        set_key(env_path, "AGENT_ENGINE_ID", engine_id)
        print(f"Updated AGENT_ENGINE_ID in .env")
    except Exception as e:
        print(f"Warning: could not update .env: {e}")


if __name__ == "__main__":
    deploy()
