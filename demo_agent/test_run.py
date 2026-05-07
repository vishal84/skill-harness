import asyncio
from google.adk.workflow import Workflow
from google.adk.agents.context import Context
from google.adk.agents import Message
from agents.report_workflow import create_report_workflow

async def main():
    wf = create_report_workflow()
    ctx = Context(messages=[Message(role="user", content="Hi")])
    async for event in wf.run(ctx=ctx, node_input=None):
        print("EVENT:", event)

if __name__ == "__main__":
    asyncio.run(main())
