import os
from e2b_code_interpreter import Sandbox
from typing import Dict, Any, Tuple

class Evaluator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("E2B_API_KEY")
        if not self.api_key:
            # For now, we might want to warn or fail if no key, 
            # but let's assume it's in env for the MVP.
            pass

    def run_in_sandbox(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Executes the provided Python code in an E2B sandbox.
        Returns a dictionary with stdout, stderr, and execution status.
        """
        print(f"Executing code in E2B sandbox (timeout={timeout}s)...")
        
        try:
            with Sandbox(api_key=self.api_key) as sandbox:
                # We can install dependencies if needed, but let's assume standard ones for now
                # or parse them from the code. For MVP, we rely on pre-installed or pip install in code.
                
                # Execute the code
                execution = sandbox.run_code(code)
                
                result = {
                    "stdout": execution.logs.stdout,
                    "stderr": execution.logs.stderr,
                    "error": execution.error,
                    "success": not execution.error
                }
                
                return result
                
        except Exception as e:
            return {
                "stdout": [],
                "stderr": [str(e)],
                "error": {"name": "SandboxError", "value": str(e), "traceback": ""},
                "success": False
            }

if __name__ == "__main__":
    # Simple test
    evaluator = Evaluator()
    res = evaluator.run_in_sandbox("print('Hello from E2B')")
    print(res)
