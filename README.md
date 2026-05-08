# ADK 2.0 Report Generation Agent

A graph-based, multi-agent report generation workflow built on [Google Agent Development Kit (ADK) 2.0](https://google.github.io/adk-docs/). Given a topic, the agent autonomously searches the web, gathers data, and synthesizes findings into a structured markdown table — all orchestrated as a deterministic DAG with intent-driven routing.

## Key Features

- **Intent-Driven Routing** — Automatically classifies user input as a report request or general inquiry, routing to the appropriate workflow branch
- **Multi-Agent Research Pipeline** — Chains five specialized LLM agents: intent analysis → web search → report writing → UI formatting
- **Structured Markdown Output** — Produces scannable, citation-rich markdown tables optimized for chat UIs
- **One-Command Deployment** — Deploy to Vertex AI Agent Engine with a single `python deploy.py` command
- **Gemini Enterprise Integration** — Register the deployed agent to Gemini Enterprise via the Discovery Engine API
- **Local Dev UI** — Interactive graph visualization and testing via `adk web`
- **PDF Export** — Optional local PDF export of generated reports

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Environment Variables](#environment-variables)
- [Available Scripts](#available-scripts)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Tech Stack

- **Language**: Python 3.13+
- **Agent Framework**: [Google ADK 2.0](https://google.github.io/adk-docs/) (`google-adk >= 2.0.0b1`)
- **LLM**: Gemini 2.5 Pro via Vertex AI
- **Cloud Platform**: Google Cloud (Vertex AI Agent Engine)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Build System**: Hatchling
- **PDF Export**: pdfkit + wkhtmltopdf (optional, local only)
- **Deployment Target**: Vertex AI Agent Engine (Reasoning Engine)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13 or higher** — required by `pyproject.toml`
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **[Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)** — for authentication and deployment
- **A Google Cloud project** with the following APIs enabled:
  - Vertex AI API (`aiplatform.googleapis.com`)
  - Cloud Storage API (`storage.googleapis.com`)
- **wkhtmltopdf** (optional) — only needed for PDF export (`brew install wkhtmltopdf` on macOS)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/vishal84/skill-harness.git
cd skill-harness/demo_agent
```

### 2. Install Dependencies

uv will automatically create a virtual environment and install everything:

```bash
uv sync
```

This reads `pyproject.toml` and installs:
- `google-adk` — the Agent Development Kit
- `markdown` — for markdown-to-HTML conversion
- `pdfkit` — for optional PDF export
- `requests` — HTTP client for API registration

### 3. Authenticate with Google Cloud

Set up Application Default Credentials (ADC) so the agent can call Vertex AI:

```bash
# Log in to gcloud
gcloud auth login

# Set your project
gcloud config set project <YOUR_GCP_PROJECT_ID>

# Create Application Default Credentials
gcloud auth application-default login

# Set the quota project (critical for API billing)
gcloud auth application-default set-quota-project <YOUR_GCP_PROJECT_ID>
```

### 4. Configure Environment Variables

Create a `.env` file in the `demo_agent/` directory:

```bash
# GCP Project ID for LLM calls
GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=1
```

See the [Environment Variables](#environment-variables) section for the full reference.

### 5. Start the ADK Dev UI

Launch the interactive development server with graph visualization:

```bash
uv run adk web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. You'll see:
- A visual graph of the agent workflow (nodes, edges, routes)
- A chat interface to test prompts interactively
- Trace/debug views for each agent invocation

### 6. Try It Out

In the ADK Dev UI chat, try these prompts:

| Prompt | Expected Branch |
|--------|----------------|
| `"Generate a report on the latest advancements in solid-state batteries"` | `generate_report` → full pipeline |
| `"What can you do?"` | `guidance` → capabilities overview |
| `"Research the top 5 AI startups in 2026"` | `generate_report` → full pipeline |
| `"Hi there"` | `guidance` → capabilities overview |

## Architecture

### Directory Structure

```
skill-harness/
├── .agent/                        # Agent skills (README generator, etc.)
├── .gitignore
├── README.md                      # This file
├── skill-harness.code-workspace   # VS Code workspace config
└── demo_agent/
    ├── .env                       # Environment variables (git-ignored)
    ├── .python-version            # Python 3.13
    ├── pyproject.toml             # Dependencies and build config
    ├── uv.lock                    # Locked dependency graph
    ├── deploy.py                  # Deploy to Vertex AI Agent Engine
    ├── register_to_ge.py          # Register to Gemini Enterprise
    ├── main.py                    # CLI entry point (local runs)
    ├── test_run.py                # Quick workflow validation script
    └── src/
        ├── __init__.py
        ├── agent.py               # ADK entry point (exports root_agent)
        ├── main.py                # CLI runner with PDF export option
        ├── requirements.txt       # Server-side requirements for Agent Engine
        ├── agents/
        │   ├── __init__.py
        │   └── report_workflow.py # Core workflow: graph definition + all agents
        └── utils/
            ├── __init__.py
            └── pdf_exporter.py    # Markdown → PDF conversion (local only)
```

### Workflow Graph

The agent uses an ADK 2.0 `Workflow` — a directed acyclic graph (DAG) that deterministically routes execution:

```
START
  │
  ▼
┌─────────────────┐
│ IntentAnalyzer  │  Classifies user input → "generate_report" or "guidance"
│ (LlmAgent)      │  Output stored in ctx.state["intent_route"]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ IntentRouter    │  Reads state, emits EventActions(route=...)
│ (FunctionNode)  │
└──┬───────────┬──┘
   │           │
   │ route:    │ route:
   │ generate  │ guidance
   │ _report   │
   ▼           ▼
┌──────────┐ ┌──────────────┐
│WebSearch │ │GuidanceAgent │  Explains capabilities,
│Agent     │ │(LlmAgent)    │  invites user to ask
│(LlmAgent)│ └──────────────┘  for a report
└────┬─────┘
     │
     ▼
┌─────────────────┐
│ReportGenerator  │  Writes comprehensive report with
│(LlmAgent)       │  title, executive summary, findings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│UISynthesizer    │  Formats as markdown table:
│(LlmAgent)       │  | # | Category | Finding | Source |
└─────────────────┘
```

### Agent Descriptions

| Agent | Type | Model | Role |
|-------|------|-------|------|
| **IntentAnalyzer** | `LlmAgent` | `gemini-2.5-pro` | Classifies user intent into `generate_report` or `guidance` |
| **IntentRouter** | `FunctionNode` | — | Reads `ctx.state["intent_route"]` and emits a route event |
| **GuidanceAgent** | `LlmAgent` | `gemini-2.5-pro` | Explains agent capabilities when no report is requested |
| **WebSearchAgent** | `LlmAgent` | `gemini-2.5-pro` | Searches the web for data points on the requested topic |
| **ReportGenerator** | `LlmAgent` | `gemini-2.5-pro` | Writes a structured report with citations |
| **UISynthesizer** | `LlmAgent` | `gemini-2.5-pro` | Transforms the report into a scannable markdown table |

### Data Flow

```
User Message
  → IntentAnalyzer (LLM classifies intent)
  → IntentRouter (deterministic routing via FunctionNode)
  → [generate_report branch]
       → WebSearchAgent (gathers 8–10 cited data points)
       → ReportGenerator (writes structured report)
       → UISynthesizer (formats as markdown table)
       → Chat UI displays table
  → [guidance branch]
       → GuidanceAgent (explains capabilities)
       → Chat UI displays guidance
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID for Vertex AI calls | `my-gcp-project` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |
| `GOOGLE_GENAI_USE_VERTEXAI` | Enable Vertex AI backend (must be `1`) | `1` |

### Required for Deployment

| Variable | Description | Example |
|----------|-------------|---------|
| `STAGING_BUCKET` | GCS bucket for Agent Engine staging | `gs://my-staging-bucket` |

### Auto-Populated After Deployment

| Variable | Description | Example |
|----------|-------------|---------|
| `AGENT_ENGINE_ID` | Full resource name of the deployed engine (written by `deploy.py`) | `projects/123/locations/us-central1/reasoningEngines/456` |

### Optional — Gemini Enterprise Registration

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_ENTERPRISE_APP_ID` | Gemini Enterprise app ID for agent registration | `gemini-enterprise-xxx_xxx` |
| `GOOGLE_CLOUD_PROJECT_NUMBER` | Numeric project number (auto-resolved if not set) | `473900759553` |

## Available Scripts

All commands should be run from the `demo_agent/` directory.

| Command | Description |
|---------|-------------|
| `uv sync` | Install all dependencies into `.venv` |
| `uv run adk web` | Launch the ADK Dev UI with graph visualization at `http://127.0.0.1:8000` |
| `uv run python deploy.py` | Deploy the agent to Vertex AI Agent Engine |
| `uv run python register_to_ge.py` | Register the deployed agent to Gemini Enterprise |
| `uv run python src/main.py` | Run the workflow from the CLI with a default prompt |
| `uv run python src/main.py --prompt "..."` | Run the workflow with a custom prompt |
| `uv run python src/main.py --export-pdf` | Run the workflow and export the result to PDF |
| `uv run python test_run.py` | Quick validation of workflow execution |

## Deployment

### Deploy to Vertex AI Agent Engine

The `deploy.py` script packages the agent and deploys it as a [Reasoning Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview) on Vertex AI.

#### Prerequisites

1. **Authenticate** — ensure ADC is configured:
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project <YOUR_PROJECT>
   ```

2. **Set the staging bucket** — add `STAGING_BUCKET` to your `.env`:
   ```
   STAGING_BUCKET=gs://your-staging-bucket
   ```
   If the bucket doesn't exist, create it:
   ```bash
   gcloud storage buckets create gs://your-staging-bucket \
     --project=<YOUR_PROJECT> \
     --location=us-central1
   ```

3. **Enable APIs**:
   ```bash
   gcloud services enable aiplatform.googleapis.com storage.googleapis.com \
     --project=<YOUR_PROJECT>
   ```

#### Deploy

```bash
uv run python deploy.py
```

On success, the script:
1. Packages the `src/` directory and uploads it to GCS
2. Creates a new Agent Engine (Reasoning Engine) resource
3. Writes the `AGENT_ENGINE_ID` back to `.env` for future updates

Subsequent runs will **update** the existing engine (using the saved `AGENT_ENGINE_ID`) rather than creating a new one.

#### Monitor

View deployment logs in the GCP Console:
```
https://console.cloud.google.com/logs/query?project=<YOUR_PROJECT>&query=resource.type%3D%22aiplatform.googleapis.com%2FReasoningEngine%22
```

### Register to Gemini Enterprise (Optional)

After deploying, you can register the agent to a Gemini Enterprise app so it appears in the agent gallery:

```bash
uv run python register_to_ge.py
```

This requires `GEMINI_ENTERPRISE_APP_ID` in your `.env`. The script calls the Discovery Engine API to register the agent with its display name and description.

## Troubleshooting

### Authentication Errors

**Error**: `403 Project <name> has been deleted` or `PermissionDenied`

**Solution**: Your ADC quota project is stale. Reset it:
```bash
gcloud config set project <YOUR_PROJECT>
gcloud auth application-default login
gcloud auth application-default set-quota-project <YOUR_PROJECT>
```

### GCS Bucket Not Found

**Error**: `404 POST https://storage.googleapis.com/storage/v1/b?project=... The requested project was not found.`

**Solution**: Enable the Cloud Storage API and create the bucket manually:
```bash
gcloud services enable storage.googleapis.com --project=<YOUR_PROJECT>
gcloud storage buckets create gs://your-bucket --project=<YOUR_PROJECT> --location=us-central1
```

### Dependency Conflicts During Deployment

**Error**: `The user requested google-adk>=2.0.0b1 ... google-cloud-aiplatform[adk] depends on google-adk<2.0.0`

**Solution**: Do **not** include `[adk]` as an extra in `google-cloud-aiplatform`. Use only `[agent_engines]`:
```python
requirements=[
    "google-adk==2.0.0b1",
    "google-cloud-aiplatform[agent_engines]>=1.148.1",
]
```

### `ModuleNotFoundError: No module named 'agents'` on Agent Engine

**Solution**: The deploy script must import via `src.agents.report_workflow` (not `agents.report_workflow`) so that `cloudpickle` records module paths that match the server's `extra_packages=["./src"]` layout. Ensure `deploy.py` has:
```python
sys.path.insert(0, SCRIPT_DIR)  # NOT SRC_DIR
from src.agents.report_workflow import create_report_workflow
```

### `Invalid app name` (Pydantic Validation Error)

**Error**: `Invalid app name '7237412694289022976': must be a valid identifier`

**Solution**: Wrap the agent in an explicit `App` before passing to `AdkApp`:
```python
from google.adk.apps import App
app = App(name="report_generation_workflow", root_agent=root_agent)
deployment_app = AdkApp(app=app, enable_tracing=True)
```

### ADK Web UI Not Loading

**Solution**: Make sure you're running from the correct directory and the `.env` file exists:
```bash
cd demo_agent
uv run adk web
```

### PDF Export Fails

**Error**: `Failed to export to PDF. Make sure wkhtmltopdf is installed`

**Solution**: Install the system dependency:
```bash
# macOS
brew install wkhtmltopdf

# Ubuntu/Debian
sudo apt-get install wkhtmltopdf
```

> **Note**: PDF export is a local-only feature and is not available when the agent is deployed to Agent Engine.
