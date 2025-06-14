# AutoGen + Claude Code Integration

A comprehensive framework for integrating Microsoft's AutoGen with Anthropic's Claude Code CLI, enabling AI agents to write, execute, and manage code with full system permissions. Features real-time monitoring, interactive chat interfaces, and complete file operation tracking.

## 🚀 Overview

This project breaks the traditional limitations of AutoGen's sandboxed code execution by integrating Claude Code CLI, enabling:

- 🤖 **Multi-Agent Orchestration**: GPT-4o-mini coordinates with Claude for complex tasks
- 💻 **Unrestricted Code Execution**: Full system access for generated code
- 📝 **Smart File Management**: Automatic creation, modification, and rollback capabilities
- 🔄 **Real-time Monitoring**: Live web dashboard with Socket.IO integration
- 💬 **Interactive Chat**: Multiple web-based interfaces for agent interaction
- 📊 **Complete Tracking**: Comprehensive logging of all operations

## 🎯 Key Features

### Core Capabilities
- **Seamless AutoGen Integration**: Claude functions as a native AutoGen tool
- **Intelligent Code Parsing**: Automatic extraction and execution of code blocks
- **File Operation Tracking**: Complete history with atomic rollback support
- **Cost-Effective**: Uses GPT-4o-mini for orchestration (~$0.001/request)
- **Multiple Interfaces**: CLI, web dashboard, and interactive chat options

### Web Interfaces
- **Real-time Dashboard**: Monitor agent conversations as they happen
- **Interactive Chat**: Direct communication with AI agents
- **File Operation Viewer**: Track and rollback any file changes
- **Socket.IO Streaming**: Sub-100ms latency for live updates
- **Syntax Highlighting**: Beautiful code display with proper formatting

## 📁 Project Structure

```
autogen_claude_code/
├── Core Integration
│   ├── claude_working_demo.py      # Core Claude wrapper with file tracking
│   ├── autogen_claude_final.py     # Complete AutoGen integration
│   └── file_operation_logger.py    # File operation tracking system
│
├── Web Interfaces
│   ├── web_dashboard.py            # Real-time monitoring dashboard
│   ├── full_interactive_chat.py    # Complete chat interface
│   ├── claude_chat_final.py        # Production-ready chat
│   └── interactive_dashboard.py    # Enhanced dashboard features
│
├── Testing & Diagnostics
│   ├── test_final.py              # Integration test suite
│   ├── diagnostic_chat.py         # Socket.IO diagnostics
│   └── test_dashboard.py          # Dashboard testing
│
├── Templates
│   ├── templates/dashboard.html    # Dashboard UI
│   └── templates/interactive_chat.html # Chat interface
│
└── Configuration
    ├── .env.example               # Environment variables template
    └── requirements.txt           # Python dependencies
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

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 🚦 Quick Start

### Test the Integration
```bash
python test_final.py
```

### Run Interactive Demo
```bash
python autogen_claude_final.py
```

### Start Web Dashboard
```bash
python web_dashboard.py
# Access at http://localhost:5000
```

### Launch Interactive Chat
```bash
python full_interactive_chat.py
# Access at http://localhost:5001
```

## 💡 Usage Examples

### Basic Code Generation
```python
from claude_working_demo import claude_execute

# Generate a simple function
result = claude_execute("Write a Python function to calculate fibonacci numbers")
print(result)
```

### File Creation with Tracking
```python
# Create a file - automatically tracked and can be rolled back
result = claude_execute(
    "Create a file called app.py with a Flask hello world application. "
    "Show me the complete code."
)
```

### AutoGen Integration
```python
from autogen import AssistantAgent, UserProxyAgent, register_function
from claude_working_demo import claude_execute

# Configure AutoGen agents
config_list = [{"model": "gpt-4o-mini", "api_key": os.getenv("OPENAI_API_KEY")}]

# Create orchestrator agent
assistant = AssistantAgent(
    name="Assistant",
    llm_config={"config_list": config_list},
    system_message="You are a helpful AI assistant. Use claude_execute to generate code."
)

# Create user proxy
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    code_execution_config={"work_dir": "coding", "use_docker": False}
)

# Register Claude function
register_function(
    claude_execute,
    caller=assistant,
    executor=user_proxy,
    name="claude_execute",
    description="Use Claude to generate and execute code"
)

# Start conversation
user_proxy.initiate_chat(
    assistant,
    message="Create a Python web scraper that extracts headlines from a news website"
)
```

### Web Dashboard Integration
```python
from web_dashboard import log_agent_message, update_agent_status, monitor

# Start monitoring a conversation
monitor.start_conversation(["Assistant", "Claude", "User"])

# Log messages in real-time
log_agent_message("Assistant", "I'll help you create that web scraper", "message")
update_agent_status("Claude", "active")

# Track file operations automatically
# All file operations are logged and can be rolled back via the dashboard
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                   │
├─────────────────┬───────────────────┬───────────────────┤
│  Web Dashboard  │ Interactive Chat  │   CLI Interface   │
│   Port: 5000    │   Port: 5001     │    Direct Call    │
└────────┬────────┴────────┬──────────┴────────┬──────────┘
         │     Socket.IO    │                  │
┌────────▼─────────────────▼───────────────────▼──────────┐
│                  AutoGen Framework                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Orchestrator│  │Code Executor │  │Claude Function│  │
│  │(GPT-4o-mini)│  │ (UserProxy)  │  │  (Wrapper)    │  │
│  └─────────────┘  └──────────────┘  └───────┬───────┘  │
└──────────────────────────────────────────────┼──────────┘
                                               │
┌──────────────────────────────────────────────▼──────────┐
│                   Claude Integration                     │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ claude --print │  │Code Parser  │  │File Creator  │ │
│  │   subprocess   │  │   (regex)   │  │   (exec)     │ │
│  └────────────────┘  └─────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────┐
│                  Infrastructure Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │File Operation│  │   SocketIO   │  │   JSON       │  │
│  │   Logger     │  │  Real-time   │  │   Storage    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🔐 Security Considerations

⚠️ **CRITICAL SECURITY WARNINGS**:

1. **Full System Access**: Claude Code executes with unrestricted permissions
2. **No Sandboxing**: Generated code runs directly on your system
3. **File Operations**: Can create, modify, or delete any accessible file
4. **Network Access**: Generated code can make network requests

### Security Best Practices
- ✅ Run in isolated environments (Docker, VM)
- ✅ Review all generated code before production use
- ✅ Use file operation rollback when testing
- ✅ Monitor the dashboard during execution
- ✅ Never expose web interfaces to public internet
- ✅ Implement authentication before deployment

## 🛠️ Advanced Configuration

### Custom System Messages
```python
assistant = AssistantAgent(
    name="CodeExpert",
    system_message="""You are an expert programmer. 
    When asked to create code:
    1. Use claude_execute function
    2. Always request 'complete code'
    3. Specify filenames explicitly
    4. Include error handling
    """
)
```

### File Operation Rollback
```python
from file_operation_logger import FileOperationLogger

logger = FileOperationLogger()

# View operation history
operations = logger.get_operation_history()

# Rollback specific operation
logger.rollback_operation(operation_id)

# Rollback all operations in a session
logger.rollback_all_operations()
```

### Working Directory Control
```python
# Execute in specific directory
result = claude_execute(
    prompt="Create a Django project structure",
    working_dir="/path/to/projects"
)
```

## 🐛 Troubleshooting

### Common Issues

#### Claude CLI not found
```bash
# Ensure Claude is installed
pip install claude

# Verify installation
claude --version
```

#### Socket.IO Connection Issues
```bash
# Run diagnostics
python diagnostic_chat.py

# Check for port conflicts
lsof -i :5000
lsof -i :5001
```

#### API Key Problems
```bash
# Verify .env file
cat .env

# Test API key
python -c "import openai; print('API key configured')"
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
result = claude_execute(prompt, debug=True)
```

## 📚 API Reference

### claude_execute
```python
def claude_execute(prompt: str, working_dir: str = None, debug: bool = False) -> dict:
    """
    Execute a prompt using Claude and return results.
    
    Args:
        prompt: The instruction for Claude
        working_dir: Optional working directory
        debug: Enable debug output
        
    Returns:
        dict: {"success": bool, "output": str, "files_created": list}
    """
```

### File Operation Logger
```python
class FileOperationLogger:
    def log_operation(operation_type: str, file_path: str, content: str = None)
    def rollback_operation(operation_id: str) -> bool
    def get_operation_history(limit: int = 100) -> list
    def rollback_all_operations() -> int
```

## 🤝 Contributing

We welcome contributions! Key areas for improvement:

- 🌐 Multi-language support (currently Python-focused)
- 🔒 Sandboxing implementation
- 🔐 Authentication system for web interfaces
- 📱 Mobile-responsive UI
- 🧪 Expanded test coverage
- 📖 Additional documentation and examples

### Development Setup
```bash
# Clone the repo
git clone git@github.com:JeremyWhittaker/autogen_claude_code.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -r requirements.txt
pip install -e .
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **Microsoft AutoGen Team** - For the powerful multi-agent framework
- **Anthropic** - For Claude and the Claude Code CLI
- **Open Source Community** - For invaluable feedback and contributions

## 📞 Support

- 📧 Issues: [GitHub Issues](https://github.com/JeremyWhittaker/autogen_claude_code/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/JeremyWhittaker/autogen_claude_code/discussions)
- 📖 Documentation: [Project Wiki](https://github.com/JeremyWhittaker/autogen_claude_code/wiki)

---

**⚡ Built with passion by developers, for developers**

*Note: This is an experimental integration. Always review generated code and test thoroughly before production use.*