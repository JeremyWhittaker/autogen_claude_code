#!/usr/bin/env python3
"""
Simple test of AutoGen + Claude integration
"""

import os
from dotenv import load_dotenv
import autogen
from claude_working_demo import claude_execute

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not api_key:
    print("ERROR: OpenAI API key not found in .env file")
    exit(1)

print(f"Using API key: {api_key[:10]}...")

# LLM configuration
config_list = [{
    "model": "gpt-4o-mini",
    "api_key": api_key
}]

# Create the function definition for AutoGen
functions = [
    {
        "name": "claude_execute",
        "description": "Use Claude to generate code for the given prompt",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to send to Claude"
                }
            },
            "required": ["prompt"]
        }
    }
]

# Create orchestrator agent with function definitions
orchestrator = autogen.AssistantAgent(
    name="Orchestrator",
    llm_config={
        "config_list": config_list,
        "temperature": 0.7,
        "functions": functions
    },
    system_message="""You are an AI orchestrator that helps users with coding tasks.
    When users ask you to write code, use the claude_execute function to generate code.
    Always call the function with a clear prompt that includes 'Show me the complete code'.
    """
)

# Create code executor agent
code_executor = autogen.UserProxyAgent(
    name="CodeExecutor",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={
        "work_dir": "./generated_code",
        "use_docker": False
    }
)

# Wrapper function to ensure proper return format
def claude_execute_wrapper(prompt: str) -> str:
    """Wrapper for claude_execute that ensures proper return format"""
    print(f"\n🔧 Claude execute called with prompt: {prompt[:100]}...")
    try:
        result = claude_execute(prompt)
        print(f"✅ Claude returned: {result[:200]}...")
        return result
    except Exception as e:
        print(f"❌ Error in claude_execute: {e}")
        return f"Error calling Claude: {str(e)}"

# Register the function with the executor
code_executor.register_function(
    function_map={
        "claude_execute": claude_execute_wrapper
    }
)

# Test message
test_message = "Write a Python program that multiplies two numbers. Show me the complete code."

print("\n" + "="*60)
print("Testing AutoGen + Claude Integration")
print("="*60)
print(f"\nUser message: {test_message}\n")

# Start the conversation
try:
    code_executor.initiate_chat(
        orchestrator,
        message=test_message
    )
    print("\n✅ Test completed successfully!")
except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()