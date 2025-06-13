#!/usr/bin/env python3
"""
Simplified AutoGen + Claude Code integration demo.
Uses a single GPT-4o-mini agent that can call Claude Code as a tool.
"""

import os
from autogen import AssistantAgent, UserProxyAgent, config_list_from_dotenv
from claude_chat import claude_code_chat

# Load configuration for GPT-4o-mini (low cost model)
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

# Create assistant that uses Claude Code as a tool
assistant = AssistantAgent(
    name="Assistant",
    llm_config={
        "config_list": config_list,
        "temperature": 0.7
    },
    system_message="""You are an AI assistant that MUST use Claude Code for ALL coding tasks.

IMPORTANT: When the user asks for ANY code generation or file creation:
1. You MUST call the call_claude_code function
2. Pass the conversation as messages in format: [{"role": "user", "content": "the request"}]
3. The repo parameter is optional (defaults to current directory)

DO NOT write code yourself. ALWAYS delegate to call_claude_code for:
- Creating files
- Writing scripts  
- Code generation
- File operations

You have access to this function:
- call_claude_code(messages, repo) - Calls Claude Code to generate code

Only answer simple non-coding questions directly."""
)

# Create a wrapper function with proper typing and description
def call_claude_code(messages: list, repo: str = None) -> str:
    """
    Call Claude Code to generate code or create files.
    
    Args:
        messages: List of conversation messages in format [{"role": "user", "content": "..."}]
        repo: Working directory (defaults to current directory)
    
    Returns:
        Claude's response as a string
    """
    if repo is None:
        repo = os.getcwd()
    
    result = claude_code_chat(messages, repo)
    
    # Extract the last message from Claude
    if result and len(result) > len(messages):
        return result[-1].get("content", "No response from Claude")
    return "No response from Claude"

# Register Claude Code as a function the assistant can call
assistant.register_function(
    function_map={
        "call_claude_code": call_claude_code
    }
)

if __name__ == "__main__":
    print("=== AutoGen + Claude Code Demo ===")
    print("Using GPT-4o-mini (low cost) to orchestrate Claude Code for complex tasks.")
    print("Type 'exit' to quit.\n")
    
    # Start conversation
    user_proxy.initiate_chat(
        assistant,
        message="I need help creating a simple Python script that reads a CSV file and calculates the average of a numeric column. Can you help?"
    )