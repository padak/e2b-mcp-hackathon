"""
E2B Sandbox Demo with Claude Agent SDK

This script:
1. Creates an E2B sandbox with a Flask web UI
2. Exposes the UI via public URL
3. When button is clicked, runs Claude Agent SDK to analyze a file
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

load_dotenv()


def read_local_file(filename: str) -> str:
    """Read a local file and return its contents."""
    file_path = Path(__file__).parent / filename
    with open(file_path, 'r') as f:
        return f.read()


def create_sandbox_with_ui():
    """Create and configure the E2B sandbox with web UI."""

    print("Creating E2B sandbox...", flush=True)
    sandbox = Sandbox.create(timeout=1800)  # 30 minutes

    info = sandbox.get_info()
    print(f"Sandbox created: {info.sandbox_id}", flush=True)

    # Upload files to sandbox
    print("Uploading files to sandbox...", flush=True)

    # Upload the UI server
    ui_server_code = read_local_file('ui_server.py')
    sandbox.files.write('/home/user/ui_server.py', ui_server_code)

    # Upload the agent task script
    agent_task_code = read_local_file('agent_task.py')
    sandbox.files.write('/home/user/agent_task.py', agent_task_code)

    # Upload the test file for analysis
    test_file_content = read_local_file('test_file.txt')
    sandbox.files.write('/home/user/test_file.txt', test_file_content)

    print("Files uploaded successfully!", flush=True)

    # Install required packages
    print("Installing dependencies...", flush=True)
    sandbox.commands.run("pip install flask claude-agent-sdk e2b-code-interpreter python-dotenv", timeout=180)
    print("Dependencies installed!", flush=True)

    # Set API keys for the sandbox environment
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    e2b_key = os.getenv('E2B_API_KEY')

    if not anthropic_key:
        print("WARNING: ANTHROPIC_API_KEY not set - agent tasks will fail!", flush=True)
    if not e2b_key:
        print("WARNING: E2B_API_KEY not set - sandbox creation will fail!", flush=True)

    # Start the Flask server in background with both API keys
    print("Starting Flask UI server...", flush=True)
    flask_process = sandbox.commands.run(
        f"ANTHROPIC_API_KEY={anthropic_key} E2B_API_KEY={e2b_key} python -u /home/user/ui_server.py",
        background=True
    )

    # Wait for server to start and check if it's running
    time.sleep(5)

    # Check if Flask is listening on port 5000
    check_result = sandbox.commands.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/health || echo 'FAILED'")
    print(f"Health check result: {check_result.stdout}", flush=True)

    # Also check for any Python processes
    ps_result = sandbox.commands.run("ps aux | grep python")
    print(f"Python processes:\n{ps_result.stdout}", flush=True)

    # Get public URL
    host = sandbox.get_host(5000)
    public_url = f"https://{host}"

    print("\n" + "=" * 60, flush=True)
    print("E2B SANDBOX WITH CLAUDE AGENT SDK DEMO", flush=True)
    print("=" * 60, flush=True)
    print(f"\n Web UI available at: {public_url}", flush=True)
    print("\nClick the button in the UI to run Claude Agent SDK!", flush=True)
    print("\nPress Ctrl+C to shutdown the sandbox", flush=True)
    print("=" * 60 + "\n", flush=True)

    return sandbox, public_url


def main():
    # Verify environment
    if not os.getenv('E2B_API_KEY'):
        print("ERROR: E2B_API_KEY environment variable not set!", flush=True)
        print("Get your key from: https://e2b.dev/dashboard", flush=True)
        return

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("WARNING: ANTHROPIC_API_KEY not set - agent will fail to run!", flush=True)

    sandbox = None
    try:
        sandbox, url = create_sandbox_with_ui()

        # Keep sandbox alive until user interrupts
        print("Sandbox is running. Waiting for interactions...", flush=True)
        while True:
            time.sleep(30)
            # Extend timeout to keep sandbox alive longer
            sandbox.set_timeout(1800)  # Reset to 30 more minutes

    except KeyboardInterrupt:
        print("\n\nShutting down...", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise
    finally:
        if sandbox:
            print("Killing sandbox...", flush=True)
            sandbox.kill()
            print("Sandbox terminated.", flush=True)


if __name__ == "__main__":
    main()
