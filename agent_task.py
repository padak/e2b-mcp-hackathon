"""
Claude Agent SDK task script - runs inside E2B sandbox
Analyzes a file and provides a summary
"""
import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock


async def analyze_file(file_path: str) -> str:
    """Use Claude Agent SDK to analyze a file and return summary."""

    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()

    prompt = f"""Analyze this document and provide a brief summary with key points:

{content}

Keep your response concise (under 200 words)."""

    result_text = []
    async for message in query(prompt=prompt):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_text.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.result:
                result_text.append(message.result)

    return '\n'.join(result_text) if result_text else "Analysis complete."


async def main():
    file_path = "/home/user/test_file.txt"

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print("Starting file analysis with Claude Agent SDK...")
    print("-" * 50)

    result = await analyze_file(file_path)
    print(result)
    print("-" * 50)
    print("Analysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
