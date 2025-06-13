#!/usr/bin/env python3
"""
Test the simple AutoGen + Claude integration
"""

import os
from autogen import AssistantAgent, UserProxyAgent, config_list_from_dotenv, register_function
from claude_intelligent_wrapper import claude_intelligent_execute

# Load configuration
config_list = config_list_from_dotenv(
    dotenv_file_path=".env",
    model_api_key_map={
        "gpt-4o-mini": "OPENAI_API_KEY"
    },
    filter_dict={
        "model": ["gpt-4o-mini"]
    }
)

# Create user proxy with auto-reply
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
    default_auto_reply="Thank you!"
)

# Create assistant
assistant = AssistantAgent(
    name="CodingAssistant",
    llm_config={
        "config_list": config_list,
        "temperature": 0.5
    },
    system_message="Always use claude_intelligent_execute for coding tasks. Be brief."
)

# Register function
register_function(
    claude_intelligent_execute,
    caller=assistant,
    executor=user_proxy,
    name="claude_intelligent_execute",
    description="Execute Claude Code"
)

# Test
print("=== Testing Simple AutoGen + Claude ===\n")

try:
    user_proxy.initiate_chat(
        assistant,
        message="Use Claude to create a simple hello world Python program",
        max_turns=2
    )
    print("\n✓ Test completed!")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()