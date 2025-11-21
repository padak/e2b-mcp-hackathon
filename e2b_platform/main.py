"""
E2B Sandbox Demo with Claude Agent SDK

This script:
1. Creates a MASTER sandbox with a Flask web UI
2. Exposes the UI via public URL
3. When button is clicked, creates a SLAVE sandbox to run Claude Agent SDK
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

import config

load_dotenv()


def read_local_file(filename: str) -> str:
    """Read a local file and return its contents."""
    file_path = Path(__file__).parent / filename
    with open(file_path, 'r') as f:
        return f.read()


def create_sandbox_with_ui():
    """Create and configure the MASTER sandbox with web UI."""

    print(f"Creating MASTER sandbox (template: {config.MASTER_TEMPLATE})...", flush=True)
    try:
        sandbox = Sandbox.create(template=config.MASTER_TEMPLATE, timeout=config.MASTER_TIMEOUT)
    except Exception as e:
        if config.FALLBACK_TO_DEFAULT:
            print(f"Template not found, using default: {e}", flush=True)
            sandbox = Sandbox.create(timeout=config.MASTER_TIMEOUT)
        else:
            raise

    info = sandbox.get_info()
    print(f"MASTER sandbox created: {info.sandbox_id}", flush=True)

    # Upload files to sandbox
    print("Uploading files to sandbox...", flush=True)

    # Upload the UI server
    ui_server_code = read_local_file('ui_server.py')
    sandbox.files.write(f"{config.SANDBOX_WORK_DIR}/ui_server.py", ui_server_code)

    # Upload the config file
    config_code = read_local_file('config.py')
    sandbox.files.write(f"{config.SANDBOX_WORK_DIR}/config.py", config_code)

    # Upload the agent task script
    agent_task_code = read_local_file('agent_task.py')
    sandbox.files.write(config.AGENT_SCRIPT_PATH, agent_task_code)

    # Upload the test file for analysis
    test_file_content = read_local_file('test_file.txt')
    sandbox.files.write(config.TEST_FILE_PATH, test_file_content)

    print("Files uploaded successfully!", flush=True)

    # Install required packages (skip if using template with pre-installed deps)
    if config.FORCE_PIP_INSTALL:
        print("Installing dependencies...", flush=True)
        sandbox.commands.run(
            "pip install -q flask e2b-code-interpreter python-dotenv",
            timeout=config.PIP_INSTALL_TIMEOUT
        )
    else:
        print("Installing dependencies (skipped if template has them)...", flush=True)
        sandbox.commands.run(
            "pip install -q flask e2b-code-interpreter python-dotenv 2>/dev/null || true",
            timeout=config.PIP_INSTALL_TIMEOUT
        )
    print("Dependencies ready!", flush=True)

    # Set API keys for the sandbox environment
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    e2b_key = os.getenv('E2B_API_KEY')

    if not anthropic_key:
        print("WARNING: ANTHROPIC_API_KEY not set - agent tasks will fail!", flush=True)
    if not e2b_key:
        print("WARNING: E2B_API_KEY not set - slave sandbox creation will fail!", flush=True)

    # Start the Flask server in background with both API keys
    print("Starting Flask UI server...", flush=True)
    sandbox.commands.run(
        f"ANTHROPIC_API_KEY={anthropic_key} E2B_API_KEY={e2b_key} "
        f"python -u {config.SANDBOX_WORK_DIR}/ui_server.py > {config.FLASK_LOG_PATH} 2>&1",
        background=True
    )

    # Wait for server to start
    time.sleep(8)

    # Check if Flask is listening
    check_result = sandbox.commands.run(
        f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{config.FLASK_PORT}/health || echo 'FAILED'"
    )
    print(f"Health check result: {check_result.stdout}", flush=True)

    # Show Flask logs for debugging
    log_result = sandbox.commands.run(f"cat {config.FLASK_LOG_PATH} 2>/dev/null || echo 'No log yet'")
    print(f"Flask logs:\n{log_result.stdout}", flush=True)

    # Check for Python processes
    ps_result = sandbox.commands.run("ps aux | grep python")
    print(f"Python processes:\n{ps_result.stdout}", flush=True)

    # Get public URL
    host = sandbox.get_host(config.FLASK_PORT)
    public_url = f"https://{host}"

    print("\n" + "=" * 60, flush=True)
    print("E2B SANDBOX WITH CLAUDE AGENT SDK DEMO", flush=True)
    print("=" * 60, flush=True)
    print(f"\n Web UI available at: {public_url}", flush=True)
    print(f"\n Config:", flush=True)
    print(f"   - Master template: {config.MASTER_TEMPLATE}", flush=True)
    print(f"   - Slave template:  {config.SLAVE_TEMPLATE}", flush=True)
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
        print("MASTER sandbox is running. Waiting for interactions...", flush=True)
        while True:
            time.sleep(30)
            sandbox.set_timeout(config.MASTER_TIMEOUT)

    except KeyboardInterrupt:
        print("\n\nShutting down...", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise
    finally:
        if sandbox:
            print("Killing MASTER sandbox...", flush=True)
            sandbox.kill()
            print("MASTER sandbox terminated.", flush=True)


if __name__ == "__main__":
    main()
