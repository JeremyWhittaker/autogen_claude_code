# AutoGen + Claude Code Integration

A working demonstration of integrating Microsoft's AutoGen framework with Anthropic's Claude Code CLI, enabling AI agents to write and execute code with full system permissions.

## 🚀 Overview

This project solves a key limitation in AutoGen: agents are typically restricted to sandboxed code execution. By integrating Claude Code CLI, AutoGen agents can now:

- Generate and execute code with full system access
- Create and modify files dynamically
- Run shell commands and scripts
- Build complete applications autonomously

## 🎯 Key Innovation

The integration uses Claude's `--print` flag to get generated code as text, which is then parsed and executed programmatically:

```python
# Call Claude with --print flag
cmd = ["claude", "--print", prompt]
result = subprocess.run(cmd, capture_output=True, text=True)

# Parse code blocks
code_blocks = re.findall(r'```python\n(.*?)\n```', result.stdout, re.DOTALL)

# Execute the code
exec(code, {'__builtins__': __builtins__})
```

## 📁 Project Structure

```
autogen_claude_code/
├── claude_working_demo.py      # Core Claude integration implementation
├── autogen_claude_final.py     # Complete AutoGen + Claude example
├── test_final.py              # Test suite
├── simple_autogen_claude.py   # Simplified demo
├── examples/                  # Additional examples
├── .env.example              # Environment variables template
└── requirements.txt          # Python dependencies
```

## 🔧 Installation

1. **Clone the repository:**
```bash
git clone git@github.com:JeremyWhittaker/autogen_claude_code.git
cd autogen_claude_code
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Claude CLI:**
```bash
pip install claude
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 🚦 Quick Start

### Basic Test
```bash
python test_final.py
```

### Interactive Demo
```bash
python autogen_claude_final.py
```

### Simple Example
```python
from autogen import AssistantAgent, UserProxyAgent, register_function
from claude_working_demo import claude_execute

# Create agents
assistant = AssistantAgent(
    name="Assistant",
    llm_config={"config_list": config_list},
    system_message="Use claude_execute to generate code."
)

user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS"
)

# Register Claude function
register_function(
    claude_execute,
    caller=assistant,
    executor=user_proxy,
    name="claude_execute",
    description="Use Claude to generate code"
)

# Start conversation
user_proxy.initiate_chat(
    assistant,
    message="Create a Python script that calculates fibonacci numbers"
)
```

## 💡 Usage Examples

### Generate a Script
```python
result = claude_execute(
    "Create a file called hello.py that prints 'Hello, World!'. "
    "Show me the complete code."
)
```

### Create a Web Application
```python
result = claude_execute(
    "Create a Flask web app in app.py with a homepage and API endpoint. "
    "Show me the complete code."
)
```

### Analyze and Refactor Code
```python
result = claude_execute(
    "Analyze the code in main.py and create an optimized version. "
    "Show me the complete refactored code."
)
```

## 🔐 Security Considerations

⚠️ **Warning**: Claude Code executes with full system permissions. 

- Run in isolated environments (Docker, VM)
- Review generated code before production use
- Don't expose to untrusted users
- Monitor file system changes

## 🛠️ How It Works

1. **AutoGen Orchestration**: GPT-4 (or other LLM) coordinates the task
2. **Claude Integration**: When code is needed, AutoGen calls `claude_execute`
3. **Code Generation**: Claude generates code based on the prompt
4. **Parsing**: The system extracts code blocks from Claude's response
5. **Execution**: Code is executed using Python's `exec()`
6. **Results**: Output is returned to AutoGen for further processing

## 📊 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   User      │────▶│   AutoGen    │────▶│   Claude    │
│             │     │ (GPT-4)      │     │   Code      │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  Function    │────▶│   Parse &   │
                    │ Registration │     │   Execute   │
                    └──────────────┘     └─────────────┘
```

## 🐛 Troubleshooting

### Claude command not found
```bash
pip install claude
```

### API Key issues
Ensure your `.env` file contains:
```
OPENAI_API_KEY=your-key-here
```

### Code execution errors
Check the generated code for syntax errors:
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Advanced Usage

### Custom System Messages
```python
assistant = AssistantAgent(
    name="Assistant",
    system_message="""You are an expert programmer. 
    When asked to create code:
    1. Use claude_execute function
    2. Always request 'complete code'
    3. Specify the filename explicitly
    """
)
```

### Error Handling
```python
try:
    result = claude_execute(prompt)
except subprocess.TimeoutExpired:
    print("Claude timed out")
except Exception as e:
    print(f"Error: {e}")
```

### Working Directory
```python
# Execute in specific directory
result = claude_execute(prompt, working_dir="/path/to/project")
```

## 🤝 Contributing

Contributions are welcome! Areas of interest:
- Multi-language support (currently Python-focused)
- Improved error handling
- Sandbox execution options
- Additional examples
- Test coverage

## 📝 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Microsoft AutoGen team
- Anthropic for Claude and Claude Code CLI
- Open source community

---

**Note**: This is an experimental integration. Always review and test generated code thoroughly before use in production environments.