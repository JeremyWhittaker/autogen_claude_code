#!/usr/bin/env python3
"""
Simple, working AutoGen + Claude integration.
Single assistant that directly calls Claude with intelligent decision making.
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

# Create user proxy
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    code_execution_config=False
)

# Create a single assistant that uses Claude
assistant = AssistantAgent(
    name="CodingAssistant",
    llm_config={
        "config_list": config_list,
        "temperature": 0.5
    },
    system_message="""You are a coding assistant that uses Claude Code for all programming tasks.

When the user asks for code generation:
1. IMMEDIATELY call claude_intelligent_execute with their exact request
2. Claude will handle file creation and code generation
3. Report the results back to the user

Do not write code yourself. Always use claude_intelligent_execute for any coding task.
Keep your responses brief - just explain you're using Claude and then show the results."""
)

# Register Claude function
register_function(
    claude_intelligent_execute,
    caller=assistant,
    executor=user_proxy,
    name="claude_intelligent_execute",
    description="Execute Claude Code with intelligent handling of all prompts and permissions"
)

if __name__ == "__main__":
    print("=== Simple AutoGen + Claude Demo ===")
    print("This assistant uses Claude for all coding tasks")
    print("Type 'exit' to quit\n")
    
    # Example starter
    user_proxy.initiate_chat(
        assistant,
        message="Create a Python program that takes an input and multiplies it by 10"
    )