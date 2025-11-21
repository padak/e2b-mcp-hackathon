import sys
import os
import argparse
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

from n8n_agent.utils import load_workflow, parse_workflow, get_workflow_summary
from n8n_agent.generator import Generator
from n8n_agent.evaluator import Evaluator

def main():
    parser = argparse.ArgumentParser(description="n8n to Python Agentic Transpiler")
    parser.add_argument("workflow_file", help="Path to the n8n workflow JSON file")
    parser.add_argument("--output", "-o", help="Output path for the generated Python script", default="generated_agent.py")
    parser.add_argument("--max-retries", type=int, default=5, help="Maximum number of fix iterations")
    parser.add_argument("--api-key", help="Anthropic API Key (optional, can use env var)")
    
    args = parser.parse_args()
    
    # 1. Load and Parse
    print(f"Loading workflow from {args.workflow_file}...")
    try:
        workflow_data = load_workflow(args.workflow_file)
        workflow = parse_workflow(workflow_data)
        summary = get_workflow_summary(workflow)
        print("Workflow parsed successfully.")
    except Exception as e:
        print(f"Error parsing workflow: {e}")
        sys.exit(1)

    # Initialize components
    generator = Generator(api_key=args.api_key)
    evaluator = Evaluator()

    # 2. Analyze
    print("\nAnalyzing workflow intent...")
    intent = generator.analyze_workflow(summary)
    print(f"Intent detected: {intent}")

    # 3. Generate Initial Code
    print("\nGenerating initial Python code...")
    code = generator.generate_code(intent, summary)
    
    # 4. Iterative Execution Loop
    print(f"\nEntering execution loop (Max retries: {args.max_retries})...")
    
    for i in range(args.max_retries + 1):
        print(f"\n--- Iteration {i} ---")
        
        # Execute in E2B
        result = evaluator.run_in_sandbox(code)
        
        if result["success"]:
            print("SUCCESS! The code executed successfully.")
            print("Output:")
            print(result["stdout"])
            break
        else:
            print("Execution FAILED.")
            print("Error:")
            print(result["stderr"])
            
            if i < args.max_retries:
                print("Attempting to fix code...")
                code = generator.fix_code(code, result["stderr"], result["stdout"])
            else:
                print("Max retries reached. Could not fix the code.")
                sys.exit(1)

    # 5. Save Result
    with open(args.output, "w") as f:
        f.write(code)
    print(f"\nGenerated code saved to {args.output}")

if __name__ == "__main__":
    main()
