#!/usr/bin/env python3
"""
Test script for E2B backend sandbox setup.
Tests the same flow as frontend/src/lib/e2b.ts
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from e2b_code_interpreter import Sandbox

E2B_TEMPLATE = "sim-zpicena-gateway"
GITHUB_REPO = "https://github.com/padak/e2b-mcp-hackathon.git"


async def test_backend_setup():
    """Test the E2B backend sandbox setup."""

    print("=" * 60)
    print("Testing E2B Backend Sandbox Setup")
    print("=" * 60)

    # Check env vars
    api_key = os.getenv("E2B_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")

    if not api_key:
        print("ERROR: E2B_API_KEY not set")
        return False
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return False
    if not perplexity_key:
        print("ERROR: PERPLEXITY_API_KEY not set")
        return False

    print(f"✓ Environment variables OK")

    # Create sandbox
    print(f"\n1. Creating sandbox with template: {E2B_TEMPLATE}")
    sbx = Sandbox.create(
        template=E2B_TEMPLATE,
        timeout=600,  # 10 minutes
    )
    print(f"   ✓ Sandbox created: {sbx.sandbox_id}")

    try:
        # Clone repository
        print(f"\n2. Cloning repository: {GITHUB_REPO}")
        result = sbx.commands.run(f"git clone {GITHUB_REPO} /home/user/app", timeout=60)
        if result.exit_code != 0:
            print(f"   ERROR: {result.stderr}")
            return False
        print(f"   ✓ Repository cloned")

        # Check Python version
        print("\n3. Checking default Python version...")
        result = sbx.commands.run("python3 --version", timeout=10)
        print(f"   {result.stdout.strip()}")

        # Install uv and newer Python
        print("\n3b. Installing uv and Python 3.12...")
        try:
            result = sbx.commands.run("curl -LsSf https://astral.sh/uv/install.sh | sh", timeout=60)
            if result.exit_code == 0:
                print("   ✓ uv installed")
            # Install Python 3.12
            result = sbx.commands.run("~/.local/bin/uv python install 3.12", timeout=120)
            if result.exit_code == 0:
                print("   ✓ Python 3.12 installed")
            # Check version
            result = sbx.commands.run("~/.local/bin/uv run --python 3.12 python --version", timeout=10)
            print(f"   New Python: {result.stdout.strip()}")
        except Exception as e:
            print(f"   ERROR: {e}")

        # Check what's installed
        print("\n4. Checking pre-installed packages...")
        result = sbx.commands.run("pip3 list | grep -E 'mesa|numpy|anthropic|e2b|mcp|fastapi'", timeout=30)
        print(f"   Pre-installed:\n{result.stdout}")

        # Try installing dependencies
        print("\n5. Installing dependencies...")
        packages = [
            "fastapi",
            "uvicorn",
            "e2b-code-interpreter",
            "anthropic",
            "httpx",
            "pydantic",
        ]

        for pkg in packages:
            print(f"   Installing {pkg}...", end=" ")
            try:
                result = sbx.commands.run(f"pip3 install {pkg}", timeout=120)
                if result.exit_code == 0:
                    print("✓")
                else:
                    print(f"FAILED (exit {result.exit_code})")
                    print(f"   stderr: {result.stderr[:200]}")
            except Exception as e:
                print(f"ERROR: {e}")

        # Create venv with Python 3.12 and install all packages there
        print("\n6. Creating Python 3.12 venv and installing packages...")
        try:
            # Create venv
            result = sbx.commands.run(
                "~/.local/bin/uv venv /home/user/.venv --python 3.12",
                timeout=60
            )
            if result.exit_code == 0:
                print("   ✓ .venv created")

            # Install all packages including mcp using uv
            result = sbx.commands.run(
                "~/.local/bin/uv pip install --python /home/user/.venv/bin/python fastapi uvicorn e2b-code-interpreter anthropic httpx pydantic mcp",
                timeout=180
            )
            if result.exit_code == 0:
                print("   ✓ All packages installed (including mcp)")
            else:
                print(f"   FAILED: {result.stderr[:300]}")
        except Exception as e:
            print(f"   ERROR: {e}")

        # Verify installations
        print("\n7. Verifying installations...")
        result = sbx.commands.run("pip3 list | grep -E 'fastapi|uvicorn|e2b|anthropic|mcp'", timeout=30)
        print(f"   Installed packages:\n{result.stdout}")

        # Create .env
        print("\n6. Creating .env file...")
        env_content = f"""
ANTHROPIC_API_KEY={anthropic_key}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
E2B_API_KEY={api_key}
PERPLEXITY_API_KEY={perplexity_key}
"""
        sbx.files.write("/home/user/app/.env", env_content)
        print("   ✓ .env created")

        # Test import
        print("\n7. Testing backend import...")
        result = sbx.commands.run(
            "cd /home/user/app/src && python3 -c 'from backend.api import app; print(\"Import OK\")'",
            timeout=30
        )
        if result.exit_code == 0:
            print(f"   ✓ {result.stdout.strip()}")
        else:
            print(f"   ERROR: {result.stderr}")
            return False

        # Start server in background
        print("\n8. Starting FastAPI server...")
        sbx.commands.run(
            "cd /home/user/app/src && python3 -m uvicorn backend.api:app --host 0.0.0.0 --port 8000",
            background=True
        )

        # Wait and check
        import time
        time.sleep(5)

        host = sbx.get_host(8000)
        url = f"https://{host}"
        print(f"   Backend URL: {url}")

        # Test health endpoint
        print("\n9. Testing health endpoint...")
        result = sbx.commands.run(f"curl -s {url}/health", timeout=10)
        if "ok" in result.stdout:
            print(f"   ✓ Health check passed: {result.stdout}")
        else:
            print(f"   WARNING: {result.stdout}")

        print("\n" + "=" * 60)
        print("✓ Backend setup test completed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print("\nCleaning up sandbox...")
        sbx.kill()
        print("Done.")


if __name__ == "__main__":
    success = asyncio.run(test_backend_setup())
    sys.exit(0 if success else 1)
