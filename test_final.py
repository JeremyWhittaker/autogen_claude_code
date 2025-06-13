#!/usr/bin/env python3
"""Test the final AutoGen + Claude integration"""

import os
from autogen import AssistantAgent, UserProxyAgent, config_list_from_dotenv, register_function
from claude_working_demo import claude_execute

# Load config
config_list = config_list_from_dotenv(
    dotenv_file_path=".env",
    model_api_key_map={"gpt-4o-mini": "OPENAI_API_KEY"},
    filter_dict={"model": ["gpt-4o-mini"]}
)

# Auto user
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
    default_auto_reply="Great, thank you!"
)

# Assistant
assistant = AssistantAgent(
    name="Assistant",
    llm_config={"config_list": config_list},
    system_message="Use claude_execute to create any programs requested. Include 'Show me the complete code' in your prompts to Claude."
)

# Register function
register_function(
    claude_execute,
    caller=assistant,
    executor=user_proxy,
    name="claude_execute",
    description="Use Claude to generate code"
)

print("=== Testing Final Integration ===\n")

# Test
user_proxy.initiate_chat(
    assistant,
    message="Create a program that takes input and multiplies by 10",
    max_turns=2
)

# Check for created files
import glob
py_files = glob.glob("*.py")
new_files = [f for f in py_files if "multiply" in f.lower()]
if new_files:
    print(f"\n✓ Success! Created: {new_files}")
else:
    print("\n✗ No files created")