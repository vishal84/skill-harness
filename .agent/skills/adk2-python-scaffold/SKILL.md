---
name: adk2-python-scaffold
description: "Scaffolds a new ADK 2.0 Python project with graph-based agent workflows using WorkflowAgent."
category: development
risk: safe
source: local
tags: "[adk, python, scaffolding, graph-workflow, agent]"
date_added: "2026-05-07"
---

# adk2-python-scaffold

## Purpose

To scaffold a new Python project configured for Google's Agent Development Kit (ADK) 2.0, specifically structured to build deterministic, graph-based multi-agent workflows using the `WorkflowAgent`.

## When to Use This Skill

This skill should be used when:
- The user requests to create a new ADK 2.0 project or agent.
- The user wants to build a graph-based workflow using ADK.
- The user needs an example of how to use ADK 2.0 for orchestration.

## Scaffolding Instructions

When invoked to scaffold a new project, you should create the following structure and files:

### 1. Initialize the Python Project

Create a structured directory for the project. Provide the user with the bash commands or execute them if requested:

```bash
mkdir -p src/agents
mkdir -p tests
touch src/__init__.py
touch src/agents/__init__.py
```

### 2. Populate `requirements.txt`

Create a `requirements.txt` file with the required dependencies.

**`requirements.txt`**
```text
google-adk>=2.0.0
```

### 3. Generate a Graph-Based Workflow Example

Create a file `src/agents/routing_workflow.py` using the `WorkflowAgent` and `LlmAgent` from `google.adk.agents`.

**`src/agents/routing_workflow.py`**
```python
from google.adk.agents import WorkflowAgent, LlmAgent

def create_workflow() -> WorkflowAgent:
    """
    Creates a graph-based workflow using ADK 2.0 WorkflowAgent.
    """
    # 1. Define nodes (agents)
    # The LlmAgent is used for LLM-powered tasks with specific instructions.
    classifier_agent = LlmAgent(name="Classifier", instruction="Categorize user intent as 'urgent' or 'standard'. Output only the category.")
    priority_handler = LlmAgent(name="PriorityHandler", instruction="Handle urgent requests with high priority.")
    standard_handler = LlmAgent(name="StandardHandler", instruction="Handle standard requests appropriately.")

    # 2. Define the graph (Nodes and Edges)
    routing_workflow = WorkflowAgent(
        name="routing_workflow",
        nodes=[classifier_agent, priority_handler, standard_handler],
        edges=[
            ("START", "Classifier"), # Unconditional edge starting the graph
            ("Classifier", "PriorityHandler", "urgent"), # Conditional edge: executes if classifier outputs 'urgent'
            ("Classifier", "StandardHandler", "standard") # Conditional edge: executes if classifier outputs 'standard'
        ]
    )
    
    return routing_workflow
```

### 4. Create an Entry Point

Create `src/main.py` to demonstrate how to run the workflow.

**`src/main.py`**
```python
from agents.routing_workflow import create_workflow

def main():
    print("Initializing ADK 2.0 Workflow...")
    workflow = create_workflow()
    
    user_input = "My server is down and I am losing money!"
    print(f"Running workflow with input: {user_input}")
    
    # Run the workflow
    result = workflow.run(user_input)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

## ADK 2.0 Graph Workflow Concepts

When answering questions about ADK 2.0 or modifying the code, apply these core concepts:
- **Graph-Based Workflows**: ADK 2.0 uses a Directed Acyclic Graph (DAG) for deterministic execution flow instead of simple prompt-response loops.
- **Nodes**: Units of work. These can be `LlmAgent` instances, `ToolNode` wrappers around APIs, pure Python function nodes, or human-in-the-loop (HITL) checkpoints.
- **Edges**: Tuples defining the control flow. 
  - *Unconditional*: `(Source, Destination)`
  - *Conditional*: `(Source, Destination, Condition)`
- **START**: A reserved keyword in the ADK engine to designate the entry point of the graph.

## Best Practices

- Advise the user to use Python 3.10 or higher.
- Remind the user to run `pip install -r requirements.txt` (or `pip install "google-adk>=2.0.0"`) to install the dependencies.
- ADK 2.0 might be in pre-release, so if the installation fails, suggest `pip install google-adk --pre`.
