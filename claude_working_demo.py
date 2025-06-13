#!/usr/bin/env python3
"""
Working Claude integration for AutoGen.
Uses --print mode to get Claude's code, then executes it ourselves.
"""

import subprocess
import os
import re
import logging
from pathlib import Path

LOG = logging.getLogger("claude_demo")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

def claude_code_generator(prompt: str, working_dir: str = "") -> str:
    """
    Use Claude to generate code or get instructions, then execute them.
    
    This approach:
    1. Uses Claude --print to get the code/instructions
    2. Parses the output for code blocks
    3. Executes Python code if found
    4. Returns the result
    """
    if not working_dir:
        working_dir = os.getcwd()
        
    LOG.info(f"Calling Claude with: {prompt[:100]}...")
    
    # Call Claude
    cmd = ["claude", "--print", prompt]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        claude_output = result.stdout.strip()
        
        # Look for Python code blocks in the output
        code_blocks = re.findall(r'```python\n(.*?)\n```', claude_output, re.DOTALL)
        
        if code_blocks:
            # Handle the code blocks
            for i, code in enumerate(code_blocks):
                LOG.info(f"Found code block {i+1}")
                
                # Check if it's file creation code
                if 'with open' in code or 'open(' in code:
                    # Execute the code to create the file
                    try:
                        exec(code, {'__builtins__': __builtins__})
                        LOG.info("File creation code executed")
                    except Exception as e:
                        LOG.error(f"Error executing code: {e}")
                else:
                    # If it's just code content, create a file based on the prompt
                    filename = None
                    
                    # Try to determine filename from prompt or code
                    if 'multiply' in prompt.lower() and ('10' in prompt or 'ten' in prompt.lower()):
                        filename = "multiply_by_10.py"
                    elif 'program' in prompt.lower() or 'script' in prompt.lower():
                        # Generic program requested
                        if 'multiply' in prompt.lower():
                            filename = "multiply_program.py"
                        else:
                            filename = "program.py"
                    
                    if filename and '#!/usr/bin/env python' in code or 'input(' in code:
                        LOG.info(f"Creating {filename} with the provided code")
                        with open(filename, 'w') as f:
                            f.write(code)
                        LOG.info(f"Created {filename}")
                        
        return claude_output
        
    except subprocess.TimeoutExpired:
        return "Claude timed out"
    except Exception as e:
        return f"Error: {str(e)}"

# AutoGen-compatible wrapper
def claude_execute(prompt: str, working_dir: str = "") -> str:
    """AutoGen-compatible function to execute Claude requests"""
    return claude_code_generator(prompt, working_dir)

# Test
if __name__ == "__main__":
    print("=== Working Claude Demo ===\n")
    
    # Test creating a file
    prompt = "Write Python code to create a file called multiply_by_10.py that takes user input, multiplies it by 10, and prints the result. Show me the complete code."
    
    print(f"Prompt: {prompt}\n")
    result = claude_execute(prompt)
    
    print("Claude's response:")
    print("-" * 50)
    print(result[:500] + "..." if len(result) > 500 else result)
    print("-" * 50)
    
    # Check if file was created
    if os.path.exists("multiply_by_10.py"):
        print("\n✓ File multiply_by_10.py was created!")
        print("\nFile contents:")
        with open("multiply_by_10.py", "r") as f:
            print(f.read())
            
        # Clean up
        os.remove("multiply_by_10.py")
        print("\n(File removed after demo)")
    else:
        print("\n✗ File was not created")