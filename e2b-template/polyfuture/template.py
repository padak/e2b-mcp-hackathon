from e2b import Template

template = (
    Template()
    .from_image("e2bdev/base")
    # Install uv
    .run_cmd("curl -LsSf https://astral.sh/uv/install.sh | sh")
    # Install Python 3.12
    .run_cmd("/home/user/.local/bin/uv python install 3.12")
    # Create venv with Python 3.12
    .run_cmd("/home/user/.local/bin/uv venv /home/user/.venv --python 3.12")
    # Install all required packages
    .run_cmd("/home/user/.local/bin/uv pip install --python /home/user/.venv/bin/python "
             "fastapi uvicorn e2b-code-interpreter anthropic httpx pydantic mcp "
             "python-dotenv mesa==2.1.5 numpy pandas plotly")
    # Add venv to PATH
    .set_envs({"PATH": "/home/user/.venv/bin:$PATH"})
)