import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from google.adk.workflow import Workflow
from google.adk.agents.context import Context, InvocationContext
from google.adk.agents.messages import Message
from agents.report_workflow import create_report_workflow

async def main():
    wf = create_report_workflow()
    ctx = Context()
    print("Running workflow with node_input='Hi'")
    async for event in wf.run(ctx=ctx, node_input='Hi'):
        print("EVENT:", type(event).__name__)
        if hasattr(event, 'data'):
            print("DATA:", event.data)
        if hasattr(event, 'route'):
            print("ROUTE:", event.route)

if __name__ == "__main__":
    asyncio.run(main())
