import sys
import os

# Add src to the path so that local modules can be imported if needed
sys.path.insert(0, os.path.dirname(__file__))

from agents.report_workflow import create_report_workflow

# The adk web server looks for a 'root_agent' variable in src/agent.py
root_agent = create_report_workflow()
