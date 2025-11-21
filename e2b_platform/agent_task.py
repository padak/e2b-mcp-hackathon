"""
Claude Agent SDK task script - runs inside E2B sandbox
Analyzes a file using configured model and settings
"""
import asyncio
import os
import json
from claude_agent_sdk import query, ClaudeAgentOptions


def load_runtime_config():
    """Load runtime configuration from JSON file."""
    config_path = '/home/user/runtime_config.json'
    default_config = {
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 200000,
        'system_prompt': 'You are a helpful document analyst.',
        'analysis_prompt': 'Analyze this document:\n\n{content}'
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")

    return default_config


def extract_text_from_message(message) -> str:
    """Extract clean text content from SDK message objects."""
    # Get the class name to determine message type
    msg_type = type(message).__name__

    if msg_type == 'AssistantMessage':
        # AssistantMessage has content array with TextBlock objects
        if hasattr(message, 'content') and message.content:
            texts = []
            for block in message.content:
                if hasattr(block, 'text'):
                    texts.append(block.text)
            return '\n'.join(texts)

    elif msg_type == 'ResultMessage':
        # ResultMessage has a result field with the final text
        if hasattr(message, 'result') and message.result:
            return message.result

    # Skip SystemMessage and other message types
    return ''


async def analyze_file(file_path: str, runtime_config: dict) -> str:
    """Use Claude Agent SDK to analyze a file and return summary."""

    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()

    # Build the prompt from template
    prompt_template = runtime_config.get('analysis_prompt', 'Analyze this document:\n\n{content}')
    prompt = prompt_template.format(content=content)

    # Set max_tokens via environment variable (SDK doesn't expose it directly)
    max_tokens = runtime_config.get('max_tokens', 200000)
    os.environ['CLAUDE_CODE_MAX_OUTPUT_TOKENS'] = str(max_tokens)

    # Build SDK options with available parameters
    options = ClaudeAgentOptions(
        model=runtime_config.get('model', 'claude-sonnet-4-20250514'),
        system_prompt=runtime_config.get('system_prompt', 'You are a helpful document analyst.'),
        max_turns=1,  # Single turn for document analysis
    )

    result_text = None
    async for message in query(prompt=prompt, options=options):
        # Extract clean text from message objects
        text = extract_text_from_message(message)
        if text:
            # Use the last non-empty result (ResultMessage contains final output)
            result_text = text

    return result_text if result_text else "Analysis complete - no output generated."


async def main():
    file_path = "/home/user/test_file.txt"

    # Load runtime configuration
    runtime_config = load_runtime_config()

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    # Print config info (will be filtered in UI)
    print(f"Config: model={runtime_config.get('model')}, max_tokens={runtime_config.get('max_tokens')}")

    # Run analysis
    result = await analyze_file(file_path, runtime_config)

    # Output with clear markers
    print("=" * 50)
    print("ANALYSIS RESULT")
    print("=" * 50)
    print(result)
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
