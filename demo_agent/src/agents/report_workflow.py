from google.adk.agents import LlmAgent
from google.adk.workflow import Workflow, Edge, START

def create_report_workflow() -> Workflow:
    """
    Creates a graph-based workflow using ADK 2.0 Workflow 
    to generate research reports.
    """
    
    # 1. Intent Analyzer
    # Understands if the user wants to generate a report on a topic.
    intent_analyzer = LlmAgent(
        name="IntentAnalyzer",
        instruction=(
            "Analyze the user's prompt. "
            "If it is a request to generate a report or gather information on a topic, "
            "output ONLY the exact string 'generate_report'. "
            "If the user is asking what you can do, for help, or general guidance, "
            "output ONLY the exact string 'guidance'."
        )
    )

    # 1.5 Guidance Agent
    # Provides help and explains capabilities to the user.
    guidance_agent = LlmAgent(
        name="GuidanceAgent",
        instruction=(
            "You are a helpful assistant. The user is asking what you can do. "
            "Explain that you are a Report Generation Workflow Agent. "
            "You can research any topic by searching the web, gather relevant data points, "
            "and synthesize a fully formatted Markdown report with citations. "
            "Provide guidance to the user to just ask for a report on their desired topic."
        )
    )

    # 2. Web Search Subagent (Task Mode)
    # Searches the web for relevant data points and cites sources.
    web_search_agent = LlmAgent(
        name="WebSearchAgent",
        instruction=(
            "You are a web search subagent in task mode. "
            "Search for relevant data points on the provided topic. "
            "Return the collected data, ensuring that every data point "
            "is paired with source information to cite later."
        )
    )

    # 3. Report Generator Subagent (Task Mode)
    # Creates a report with a specific format.
    report_generator = LlmAgent(
        name="ReportGenerator",
        instruction=(
            "You are a report generator subagent in task mode. "
            "Take the data points and sources provided and create a report. "
            "The report MUST contain exactly the following format: "
            "1. Title "
            "2. Summary "
            "3. Headings for each subsection of information found from each source."
        )
    )

    # 4. UI Synthesizer
    # Synthesizes the report into a nice UI for a frontend web chat interface.
    ui_synthesizer = LlmAgent(
        name="UISynthesizer",
        instruction=(
            "Synthesize the generated report into a clean, well-formatted Markdown "
            "structure that is optimized for display in a frontend web chat interface "
            "for human review. Ensure clear typography and spacing."
        )
    )

    # 5. Define the Graph (Nodes and Edges)
    workflow = Workflow(
        name="report_generation_workflow",
        edges=[
            Edge(from_node=START, to_node=intent_analyzer),
            Edge(from_node=intent_analyzer, to_node=web_search_agent, route="generate_report"),
            Edge(from_node=intent_analyzer, to_node=guidance_agent, route="guidance"),
            Edge(from_node=web_search_agent, to_node=report_generator),
            Edge(from_node=report_generator, to_node=ui_synthesizer)
        ]
    )
    
    return workflow
