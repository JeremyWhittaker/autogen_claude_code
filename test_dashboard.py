#!/usr/bin/env python3
"""
Test script for the web dashboard.
Runs the dashboard and simulates some agent activity.
"""

import time
import threading
from web_dashboard import app, socketio, log_agent_message, update_agent_status, monitor
from file_operation_logger import FileOperationLogger

def simulate_agent_activity():
    """Simulate some agent conversations and file operations."""
    time.sleep(3)  # Wait for server to start
    
    print("Starting simulated agent activity...")
    
    # Start a conversation
    conv_id = monitor.start_conversation(["GPT-4", "Claude", "CodeExecutor"])
    print(f"Started conversation: {conv_id}")
    
    # Simulate some messages
    messages = [
        ("GPT-4", "Let's create a Python script to calculate fibonacci numbers."),
        ("Claude", "I'll create a fibonacci calculator for you."),
        ("Claude", "```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\n# Test the function\nfor i in range(10):\n    print(f'F({i}) = {fibonacci(i)}')\n```"),
        ("CodeExecutor", "Executing the code..."),
        ("CodeExecutor", "Code executed successfully. Output:\nF(0) = 0\nF(1) = 1\nF(2) = 1\nF(3) = 2\nF(4) = 3\nF(5) = 5\nF(6) = 8\nF(7) = 13\nF(8) = 21\nF(9) = 34"),
        ("GPT-4", "Great! Now let's save this to a file called fibonacci.py"),
        ("Claude", "I'll save the fibonacci function to a file."),
    ]
    
    for agent, message in messages:
        log_agent_message(agent, message)
        update_agent_status(agent, "active")
        time.sleep(1)
        update_agent_status(agent, "idle")
    
    # Simulate file operations
    file_logger = FileOperationLogger()
    
    # Create a file
    content = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

if __name__ == "__main__":
    for i in range(10):
        print(f'F({i}) = {fibonacci(i)}')
"""
    
    with open("fibonacci.py", "w") as f:
        f.write(content)
    file_logger.log_create("fibonacci.py", content)
    
    log_agent_message("Claude", "Created file: fibonacci.py")
    
    # End conversation
    monitor.end_conversation()
    print("Conversation ended")
    
    # Clean up
    import os
    if os.path.exists("fibonacci.py"):
        os.unlink("fibonacci.py")

def main():
    """Run the dashboard with simulated activity."""
    print("Starting Web Dashboard Test...")
    print("Dashboard will be available at http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    # Start simulation in a separate thread
    sim_thread = threading.Thread(target=simulate_agent_activity, daemon=True)
    sim_thread.start()
    
    # Run the dashboard
    try:
        socketio.run(app, debug=False, port=5000, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")

if __name__ == "__main__":
    main()