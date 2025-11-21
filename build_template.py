"""
Build a custom E2B template with Claude Agent SDK pre-installed.

Run this script once to create the template, then use the template_id in your sandboxes.
"""

from e2b import Template


def build_claude_agent_template() -> str:
    """Build and save an E2B template with Claude Agent SDK installed."""

    template_builder = (
        Template()
        .from_python_image("3.13")  # Use Python 3.13 base image
        .set_workdir("/app")
        .apt_install(["git", "curl"])  # Common dependencies
        .pip_install([
            "claude-agent-sdk",
            "anthropic",  # Claude API client
        ])
    )

    # Build the template - this uploads to E2B and returns build info
    def log_handler(log):
        print(f"[{log.level}] {log.message}")

    print("Building template... (this may take a few minutes)")
    build_info = Template.build(
        template=template_builder,
        alias="chocho-claude-agent-py313",
        on_build_logs=log_handler,
    )

    print(f"\nTemplate built successfully!")
    print(f"Template ID: {build_info.template_id}")
    print(f"\nUse this template in your sandboxes:")
    print(f'  sandbox = Sandbox.create(template="{build_info.template_id}")')

    return build_info.template_id


if __name__ == "__main__":
    build_claude_agent_template()
