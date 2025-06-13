#!/usr/bin/env python3
"""
Simple working Claude wrapper using --print mode.
Handles permission requests by making follow-up calls.
"""

import subprocess
import os
import re
import logging
import openai
from pathlib import Path

# Setup logging
LOG = logging.getLogger("claude_simple")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# Load environment
def load_env():
    """Load .env file"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

def claude_execute_simple(prompt: str, working_dir: str = "") -> str:
    """
    Execute Claude with --print mode.
    If Claude asks for permissions, automatically approve and retry.
    """
    if not working_dir:
        working_dir = os.getcwd()
        
    LOG.info(f"Executing Claude with prompt: {prompt[:100]}...")
    
    # First attempt
    cmd = ["claude", "--print", prompt]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        
        # Check if Claude is asking for permission
        if "permission" in output.lower() or "need" in output.lower() or "allow" in output.lower():
            LOG.info("Claude needs permissions, trying with explicit approval...")
            
            # Try again with more explicit instructions
            enhanced_prompt = f"{prompt}. You have permission to create any files needed. Please proceed with the implementation."
            
            result = subprocess.run(
                ["claude", "--print", enhanced_prompt],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout.strip()
            
        # Clean any remaining ANSI codes
        output = re.sub(r'\x1b\[[0-9;]*m', '', output)
        
        return output
        
    except subprocess.TimeoutExpired:
        return "Claude timed out"
    except Exception as e:
        return f"Error: {str(e)}"

# Test
if __name__ == "__main__":
    print("=== Testing Simple Claude Wrapper ===\n")
    
    # Test 1: Simple request
    print("Test 1: Simple greeting")
    result = claude_execute_simple("Say hello")
    print(f"Result: {result}\n")
    
    # Test 2: Code generation
    print("Test 2: Code generation")
    result = claude_execute_simple("Create a Python file called multiply.py that takes user input and multiplies it by 10")
    print(f"Result: {result[:300]}...\n")
    
    # Check if file was created
    if os.path.exists("multiply.py"):
        print("✓ File multiply.py was created!")
        with open("multiply.py", "r") as f:
            print(f"Contents:\n{f.read()}")
    else:
        print("✗ File was not created")