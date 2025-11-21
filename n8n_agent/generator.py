import os
from anthropic import Anthropic
from typing import List, Dict, Any

from n8n_agent.config import CONFIG

class Generator:
    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = CONFIG.get("model", "claude-3-5-sonnet-20241022")

    def analyze_workflow(self, workflow_summary: str) -> str:
        """
        Analyzes the n8n workflow summary to extract the high-level intent.
        """
        prompt = f"""
        You are an expert automation engineer. Analyze the following n8n workflow summary and extract the high-level intent.
        Describe what the workflow does in plain English, identifying the key data sources, transformations, and destinations.
        Identify any external services (APIs, Databases) that are interacted with.

        Workflow Summary:
        {workflow_summary}
        
        Output your analysis as a concise description.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def generate_code(self, intent: str, workflow_summary: str) -> str:
        """
        Generates the initial Python script based on the intent and workflow details.
        """
        prompt = f"""
        You are an expert Python developer. Your task is to convert an n8n workflow into a standalone Python script.
        
        Goal: {intent}
        
        Workflow Details:
        {workflow_summary}
        
        Requirements:
        1. Use modern, idiomatic Python libraries (e.g., `requests`, `pandas`).
        2. The code MUST be self-contained.
        3. For authentication, assume API keys are available in `os.environ`.
        4. IMPORTANT: Since we are testing this in a sandbox, if the workflow requires external credentials that might not be present, 
           implement a "MOCK_MODE" flag. If `MOCK_MODE` is True (default), use dummy data instead of making real API calls.
           Structure the code so that switching `MOCK_MODE = False` would make it work with real APIs.
        5. Print clear outputs to stdout so we can verify execution.
        
        Output ONLY the Python code, inside a markdown code block.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        return self._extract_code(content)

    def fix_code(self, code: str, error_logs: str, stdout: str) -> str:
        """
        Fixes the Python code based on the execution error logs.
        """
        prompt = f"""
        You are fixing a Python script that failed to run.
        
        Current Code:
        ```python
        {code}
        ```
        
        Execution Error (stderr):
        {error_logs}
        
        Standard Output (stdout):
        {stdout}
        
        Task:
        Analyze the error and fix the code. 
        - If it's a missing dependency, add a `subprocess.check_call([sys.executable, "-m", "pip", "install", "package"])` at the top.
        - If it's a logic error, fix the logic.
        - If it's a data format error, adjust the parsing.
        
        Output ONLY the fixed Python code, inside a markdown code block.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        return self._extract_code(content)

    def _extract_code(self, text: str) -> str:
        """
        Helper to extract code from markdown blocks.
        """
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()
