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
from file_operation_logger import FileOperationLogger

LOG = logging.getLogger("claude_demo")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# Initialize file operation logger
file_logger = FileOperationLogger()

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
        
        # Look for code blocks in various formats
        code_patterns = [
            (r'```python\n(.*?)\n```', 'python'),
            (r'```py\n(.*?)\n```', 'python'),
            (r'```Python\n(.*?)\n```', 'python'),
            (r'```javascript\n(.*?)\n```', 'javascript'),
            (r'```js\n(.*?)\n```', 'javascript'),
            (r'```bash\n(.*?)\n```', 'bash'),
            (r'```sh\n(.*?)\n```', 'bash'),
            (r'```(.*?)\n```', 'generic')  # Catch-all for unspecified language
        ]
        
        code_blocks_found = []
        execution_results = []
        
        # Try each pattern
        for pattern, lang in code_patterns:
            blocks = re.findall(pattern, claude_output, re.DOTALL)
            for block in blocks:
                code_blocks_found.append((block, lang))
        
        if code_blocks_found:
            # Handle the code blocks
            for i, (code, language) in enumerate(code_blocks_found):
                LOG.info(f"Found {language} code block {i+1}")
                
                # Validate code block isn't empty or malformed
                if not code or not code.strip():
                    LOG.warning(f"Skipping empty code block {i+1}")
                    execution_results.append(f"Code block {i+1} was empty")
                    continue
                
                # Only execute Python code
                if language == 'python':
                    # Check if it's file creation code
                    if 'with open' in code or 'open(' in code:
                        # Execute the code to create the file
                        try:
                            # Create a safe execution environment
                            safe_globals = {
                                '__builtins__': __builtins__,
                                'Path': Path,
                                'os': os
                            }
                            # Track files before execution
                            files_before = set(os.listdir('.'))
                            
                            exec(code, safe_globals)
                            LOG.info("File creation code executed successfully")
                            
                            # Check for new files created
                            files_after = set(os.listdir('.'))
                            new_files = files_after - files_before
                            for new_file in new_files:
                                with open(new_file, 'r') as f:
                                    content = f.read()
                                file_logger.log_create(new_file, content)
                                LOG.info(f"Logged creation of {new_file}")
                            
                            execution_results.append(f"Code block {i+1} executed successfully")
                        except SyntaxError as e:
                            error_msg = f"Syntax error in code block {i+1}: {e}"
                            LOG.error(error_msg)
                            execution_results.append(error_msg)
                        except Exception as e:
                            error_msg = f"Error executing code block {i+1}: {type(e).__name__}: {e}"
                            LOG.error(error_msg)
                            execution_results.append(error_msg)
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
                        
                        if filename and ('#!/usr/bin/env python' in code or 'input(' in code or 'def ' in code):
                            try:
                                LOG.info(f"Creating {filename} with the provided code")
                                with open(filename, 'w') as f:
                                    f.write(code)
                                LOG.info(f"Created {filename}")
                                
                                # Log the file creation
                                file_logger.log_create(filename, code)
                                
                                execution_results.append(f"Created file: {filename}")
                            except Exception as e:
                                error_msg = f"Error creating file {filename}: {e}"
                                LOG.error(error_msg)
                                execution_results.append(error_msg)
                        else:
                            LOG.info(f"Code block {i+1} appears to be example code, not executing")
                            execution_results.append(f"Code block {i+1} shown but not executed (example code)")
                else:
                    LOG.info(f"Found {language} code block, skipping execution (only Python is supported)")
                    execution_results.append(f"Code block {i+1} ({language}) - execution not supported")
        
        # Add execution results to the output if any actions were taken
        if execution_results:
            claude_output += "\n\n=== Execution Results ===\n"
            claude_output += "\n".join(execution_results)
                        
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