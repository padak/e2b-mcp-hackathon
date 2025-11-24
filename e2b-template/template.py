#!/usr/bin/env python3
"""
PolyFuture Backend Template - Build System V2
Pre-configured Python 3.12 with all required packages for Monte Carlo simulations.
"""

from e2b import Sandbox

# Build template from Dockerfile
template = Sandbox.from_dockerfile(
    dockerfile="Dockerfile",
    name="polyfuture-backend",
    cpu_count=2,
    memory_mb=2048,
)

if __name__ == "__main__":
    # Build and register the template
    template_id = template.build()
    print(f"Template built successfully: {template_id}")
