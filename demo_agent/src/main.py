import os
import argparse
from agents.report_workflow import create_report_workflow
from utils.pdf_exporter import export_markdown_to_pdf

def main():
    parser = argparse.ArgumentParser(description="Run the ADK 2.0 Report Generation Workflow")
    parser.add_argument("--prompt", type=str, default="Generate a report on the latest advancements in solid-state batteries.", help="User prompt")
    parser.add_argument("--export-pdf", action="store_true", help="Export the final report to PDF")
    args = parser.parse_args()

    print("Initializing ADK 2.0 Report Workflow...")
    workflow = create_report_workflow()
    
    print(f"\nRunning workflow with prompt:\n'{args.prompt}'\n")
    
    # Run the workflow
    # Depending on the specific ADK 2.0 execution semantics, .run() returns the state/result.
    try:
        result = workflow.run(args.prompt)
        print("=== UI Synthesized Output ===")
        print(result)
        print("=============================")

        if args.export_pdf:
            print("\nExporting report to PDF...")
            output_file = "generated_report.pdf"
            export_markdown_to_pdf(result, output_file)
            print(f"Report successfully exported to {output_file}")
            
    except Exception as e:
        print(f"Workflow execution encountered an issue: {e}")
        print("Note: If 'google-adk' is not fully installed or configured with credentials, execution will fail.")

if __name__ == "__main__":
    main()
