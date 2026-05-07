from google.adk.agents import LlmAgent
from google.adk.workflow import Workflow, Edge, START, FunctionNode
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions


def route_intent(ctx) -> Event:
    """Read the intent classification from state and emit a route event."""
    raw = str(ctx.state.get("intent_route", "guidance")).strip().strip("\"'").lower()
    if "generate_report" in raw:
        return Event(actions=EventActions(route="generate_report"))
    return Event(actions=EventActions(route="guidance"))


def create_report_workflow() -> Workflow:
    """
    ADK 2.0 graph workflow:
      START -> IntentAnalyzer -> IntentRouter
        --[generate_report]--> WebSearchAgent -> ReportGenerator -> UISynthesizer
        --[guidance]---------> GuidanceAgent
    """

    # ── 1. Intent Analyzer ─────────────────────────────────────────────
    intent_analyzer = LlmAgent(
        name="IntentAnalyzer",
        model="gemini-2.5-pro",
        instruction=(
            "You are an intent classifier. Read the user's message and decide:\n"
            "• If the user wants a report, research, data, or information on a topic "
            "  → output exactly: generate_report\n"
            "• Otherwise (greetings, questions about capabilities, help, etc.) "
            "  → output exactly: guidance\n"
            "Output ONLY one of those two strings, nothing else."
        ),
        output_key="intent_route",
    )

    # ── 2. Router (FunctionNode) ───────────────────────────────────────
    intent_router = FunctionNode(
        name="IntentRouter",
        func=route_intent,
    )

    # ── 3a. Guidance Agent ─────────────────────────────────────────────
    guidance_agent = LlmAgent(
        name="GuidanceAgent",
        model="gemini-2.5-pro",
        instruction=(
            "You are a Report Generation Workflow Agent. "
            "The user hasn't asked for a specific report yet. "
            "Explain what you can do:\n"
            "  • Research any topic by searching the web\n"
            "  • Gather relevant data points with citations\n"
            "  • Synthesize findings into a structured markdown table report\n\n"
            "Invite the user to ask for a report on their desired topic. "
            "Keep your response concise and friendly."
        ),
    )

    # ── 3b. Web Search Agent ───────────────────────────────────────────
    web_search_agent = LlmAgent(
        name="WebSearchAgent",
        model="gemini-2.5-pro",
        instruction=(
            "You are a research agent. The user wants a report.\n"
            "Look at the ORIGINAL user message (not the classifier output) "
            "to determine the topic.\n"
            "Search for and collect key data points on that topic. "
            "For every fact, include the source name and URL.\n"
            "Return a structured list of findings — each item should have:\n"
            "  • Finding (the fact or data point)\n"
            "  • Source (name + URL)\n"
            "  • Category (a short label grouping related findings)\n"
            "Be thorough — aim for at least 8-10 data points."
        ),
    )

    # ── 4. Report Generator ────────────────────────────────────────────
    report_generator = LlmAgent(
        name="ReportGenerator",
        model="gemini-2.5-pro",
        instruction=(
            "You are a report writer. Take the research data provided and produce "
            "a comprehensive report with:\n"
            "  1. A clear **Title**\n"
            "  2. An **Executive Summary** (2-3 sentences)\n"
            "  3. **Key Findings** organized by category\n"
            "  4. A **Sources** section listing all references\n\n"
            "Write in clear, professional prose. "
            "Preserve all source citations inline."
        ),
    )

    # ── 5. UI Synthesizer (markdown table output) ──────────────────────
    ui_synthesizer = LlmAgent(
        name="UISynthesizer",
        model="gemini-2.5-pro",
        instruction=(
            "You are a formatting specialist. Take the report and transform it "
            "into a clean output optimized for a chat UI.\n\n"
            "Your output MUST contain:\n"
            "  1. **Title** as a level-1 heading\n"
            "  2. **Executive Summary** as a short paragraph\n"
            "  3. **A markdown table** summarizing the key findings with columns:\n"
            "     | # | Category | Finding | Source |\n"
            "     Each row is one key finding from the report.\n"
            "  4. **Sources** as a numbered list of links at the bottom\n\n"
            "The table is the primary deliverable. Make it scannable and complete. "
            "Do NOT omit findings — every data point from the report goes into the table."
        ),
    )

    # ── 6. Wire the graph ──────────────────────────────────────────────
    workflow = Workflow(
        name="report_generation_workflow",
        edges=[
            Edge(from_node=START, to_node=intent_analyzer),
            Edge(from_node=intent_analyzer, to_node=intent_router),
            Edge(from_node=intent_router, to_node=web_search_agent, route="generate_report"),
            Edge(from_node=intent_router, to_node=guidance_agent, route="guidance"),
            Edge(from_node=web_search_agent, to_node=report_generator),
            Edge(from_node=report_generator, to_node=ui_synthesizer),
        ],
    )

    return workflow
