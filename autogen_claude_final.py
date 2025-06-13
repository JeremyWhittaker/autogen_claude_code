#!/usr/bin/env python3
"""
Final working AutoGen + Claude integration.
Uses Claude to generate code and handles file creation.
"""

import os
from autogen import AssistantAgent, UserProxyAgent, config_list_from_dotenv, register_function
from claude_working_demo import claude_execute

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

# Create assistant
assistant = AssistantAgent(
    name="Assistant",
    llm_config={
        "config_list": config_list,
        "temperature": 0.5
    },
    system_message="""You are a helpful coding assistant that uses Claude for all code generation tasks.

When the user asks for code or to create a program:
1. Call claude_execute with a clear prompt that includes:
   - The filename they want (if specified)
   - What the program should do
   - Request to "show the complete code"
   
2. Claude will generate the code and our system will create the file

Example: If user wants a program that multiplies by 10, use:
"Write Python code to create a file called multiply.py that takes user input, multiplies it by 10, and prints the result. Show me the complete code."

Always be helpful and explain what you're doing."""
)

# Register Claude function
register_function(
    claude_execute,
    caller=assistant,
    executor=user_proxy,
    name="claude_execute",
    description="Use Claude to generate code and create files"
)

if __name__ == "__main__":
    print("=== AutoGen + Claude Final Demo ===")
    print("This uses GPT-4o-mini to orchestrate and Claude to generate code")
    print("Type 'exit' to quit\n")
    
    # Start the conversation
    user_proxy.initiate_chat(
        assistant,
        message="I want you to have Claude code write a program that will take an input and then multiply it by 10 and output that number"
    )