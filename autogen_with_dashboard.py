#!/usr/bin/env python3
"""
Example of AutoGen + Claude integration with web dashboard monitoring.
This shows how to integrate the monitoring dashboard with your AutoGen agents.
"""

import autogen
from autogen import AssistantAgent, UserProxyAgent
import requests
import threading
import time
from claude_working_demo import claude_execute
from web_dashboard import log_agent_message, update_agent_status, monitor

# Configuration
config_list = [
    {
        "model": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
]

llm_config = {
    "config_list": config_list,
    "temperature": 0.7,
}

class MonitoredAssistantAgent(AssistantAgent):
    """Assistant agent with dashboard monitoring."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dashboard_name = kwargs.get('name', 'Assistant')
    
    def send(self, message, recipient, request_reply=None, silent=False):
        """Override send to log messages to dashboard."""
        # Log the message to dashboard
        if isinstance(message, dict):
            content = message.get('content', str(message))
        else:
            content = str(message)
        
        log_agent_message(self.dashboard_name, content, "sent")
        update_agent_status(self.dashboard_name, "active")
        
        # Call parent method
        result = super().send(message, recipient, request_reply, silent)
        
        update_agent_status(self.dashboard_name, "idle")
        return result
    
    def receive(self, message, sender, request_reply=None, silent=False):
        """Override receive to log messages to dashboard."""
        # Log the received message
        if isinstance(message, dict):
            content = message.get('content', str(message))
        else:
            content = str(message)
        
        log_agent_message(sender.name if hasattr(sender, 'name') else str(sender), 
                         content, "received")
        
        # Call parent method
        return super().receive(message, sender, request_reply, silent)

class MonitoredUserProxyAgent(UserProxyAgent):
    """User proxy agent with dashboard monitoring."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dashboard_name = kwargs.get('name', 'UserProxy')
    
    def send(self, message, recipient, request_reply=None, silent=False):
        """Override send to log messages to dashboard."""
        if isinstance(message, dict):
            content = message.get('content', str(message))
        else:
            content = str(message)
        
        log_agent_message(self.dashboard_name, content, "sent")
        update_agent_status(self.dashboard_name, "active")
        
        result = super().send(message, recipient, request_reply, silent)
        
        update_agent_status(self.dashboard_name, "idle")
        return result

def monitored_claude_execute(prompt: str, working_dir: str = "") -> str:
    """Claude execute function with dashboard monitoring."""
    log_agent_message("Claude", f"Executing: {prompt[:100]}...", "execution")
    update_agent_status("Claude", "executing")
    
    result = claude_execute(prompt, working_dir)
    
    log_agent_message("Claude", result, "result")
    update_agent_status("Claude", "idle")
    
    return result

def start_dashboard_server():
    """Start the dashboard server in a separate thread."""
    def run_server():
        from web_dashboard import socketio, app
        socketio.run(app, port=5000, debug=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to start
    print("Dashboard started at http://localhost:5000")

def main():
    """Main function demonstrating dashboard integration."""
    print("Starting AutoGen with Dashboard Monitoring...")
    
    # Start dashboard server
    start_dashboard_server()
    
    # Start a new conversation in the monitor
    monitor.start_conversation(["Orchestrator", "CodeBot", "Claude"])
    
    # Create monitored agents
    orchestrator = MonitoredAssistantAgent(
        name="Orchestrator",
        system_message="""You are a software development orchestrator. 
        Coordinate with CodeBot to generate code using Claude.
        Keep responses concise and focused on the task.""",
        llm_config=llm_config,
    )
    
    # Create user proxy for code execution
    code_executor = MonitoredUserProxyAgent(
        name="CodeBot",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={"work_dir": "generated_code", "use_docker": False},
    )
    
    # Register Claude function
    code_executor.register_function(
        function_map={
            "claude_execute": monitored_claude_execute,
        }
    )
    
    # Example task
    task = """
    Use claude_execute to create a Python script that:
    1. Generates a list of 10 random numbers
    2. Sorts them in ascending order
    3. Prints the sorted list
    
    Name the file 'random_sorter.py'
    """
    
    # Log the task
    log_agent_message("System", f"Starting task: {task}", "task")
    
    # Initiate the conversation
    code_executor.initiate_chat(orchestrator, message=task)
    
    # End conversation monitoring
    monitor.end_conversation()
    
    print("\nTask completed! Check the dashboard at http://localhost:5000")
    print("Press Ctrl+C to exit...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    main()