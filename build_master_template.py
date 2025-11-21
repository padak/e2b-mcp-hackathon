"""
Build the master template with Flask UI and E2B SDK for orchestrating sandboxes.
"""

from e2b import Template


def build_master_template() -> str:
    """Build master template with Flask + E2B SDK."""

    template_builder = (
        Template()
        .from_python_image("3.13")
        .set_workdir("/app")
        .apt_install(["git", "curl"])
        .pip_install([
            "flask",
            "e2b",
            "e2b-code-interpreter",
            "python-dotenv",
        ])
    )

    def log_handler(log):
        print(f"[{log.level}] {log.message}")

    print("Building master template...")
    build_info = Template.build(
        template=template_builder,
        alias="chocho-master",
        on_build_logs=log_handler,
    )

    print(f"\nTemplate built successfully!")
    print(f"Template ID: {build_info.template_id}")
    return build_info.template_id


if __name__ == "__main__":
    build_master_template()
