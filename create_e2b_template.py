#!/usr/bin/env python3
"""Create custom E2B template based on mcp-gateway with Mesa dependencies."""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

# Template configuration
TEMPLATE_NAME = "mesa-mcp-gateway"
BASE_TEMPLATE = "mcp-gateway"

# Requirements from requirements-e2b.txt
REQUIREMENTS = """mesa==2.1.5
numpy
pandas
plotly
"""

def create_template():
    """Create and build E2B template."""

    # Create temporary directory for template files
    template_dir = Path(tempfile.mkdtemp(prefix="e2b_template_"))

    try:
        # Create e2b.toml
        e2b_toml = f"""# E2B Template Configuration
template_id = "{TEMPLATE_NAME}"

[template]
dockerfile = "Dockerfile"
"""
        (template_dir / "e2b.toml").write_text(e2b_toml)

        # Create Dockerfile
        dockerfile = f"""FROM e2bdev/{BASE_TEMPLATE}

# Install Python dependencies
RUN pip install --no-cache-dir \\
    mesa==2.1.5 \\
    numpy \\
    pandas \\
    plotly
"""
        (template_dir / "Dockerfile").write_text(dockerfile)

        print(f"Template files created in: {template_dir}")
        print(f"\nBuilding template '{TEMPLATE_NAME}' based on '{BASE_TEMPLATE}'...")

        # Build template using E2B CLI
        result = subprocess.run(
            ["e2b", "template", "build", "--name", TEMPLATE_NAME],
            cwd=template_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("\n✓ Template built successfully!")
            print(result.stdout)
        else:
            print("\n✗ Template build failed:")
            print(result.stderr)
            return False

        return True

    finally:
        # Cleanup
        shutil.rmtree(template_dir)
        print(f"\nCleaned up temporary files")

if __name__ == "__main__":
    # Check for E2B API key
    if not os.getenv("E2B_API_KEY"):
        from dotenv import load_dotenv
        load_dotenv()

    if not os.getenv("E2B_API_KEY"):
        print("Error: E2B_API_KEY not found in environment")
        exit(1)

    success = create_template()
    exit(0 if success else 1)
