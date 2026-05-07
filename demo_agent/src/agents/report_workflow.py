from google.adk.agents import WorkflowAgent, LlmAgent

def create_report_workflow() -> WorkflowAgent:
    """
    Creates a graph-based workflow using ADK 2.0 WorkflowAgent 
    to generate research reports.
    """
    
    # 1. Intent Analyzer
    # Understands if the user wants to generate a report on a topic.
    intent_analyzer = LlmAgent(
        name="IntentAnalyzer",
        instruction=(
            "Analyze the user's prompt. If it is a request to generate "
            "a report or gather information on a topic, extract the topic "
            "and output the intent as 'generate_report'. "
            "Otherwise, output 'standard'."
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
    workflow = WorkflowAgent(
        name="report_generation_workflow",
        nodes=[intent_analyzer, web_search_agent, report_generator, ui_synthesizer],
        edges=[
            ("START", "IntentAnalyzer"), # Unconditional edge starting the graph
            ("IntentAnalyzer", "WebSearchAgent", "generate_report"), # Conditional edge based on intent
            ("WebSearchAgent", "ReportGenerator"), # Proceed to generate the report
            ("ReportGenerator", "UISynthesizer") # Finalize formatting for the UI
        ]
    )
    
    return workflow
