#!/usr/bin/env python3
"""
Web dashboard for monitoring AutoGen + Claude Code agent conversations.
Provides real-time monitoring, conversation history, and file operation tracking.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
from pathlib import Path
import threading
import time
from collections import deque
import logging

# Import our file operation logger
from file_operation_logger import FileOperationLogger

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize components
file_logger = FileOperationLogger()
conversation_log = deque(maxlen=1000)  # Store last 1000 messages
active_agents = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_dashboard")

class ConversationMonitor:
    """Monitors and logs agent conversations."""
    
    def __init__(self):
        self.conversations = []
        self.current_conversation = None
        self.log_file = Path(".claude_logs/conversations.json")
        self.load_conversations()
    
    def load_conversations(self):
        """Load existing conversations from disk."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.conversations = json.load(f)
            except:
                self.conversations = []
    
    def save_conversations(self):
        """Save conversations to disk."""
        self.log_file.parent.mkdir(exist_ok=True)
        with open(self.log_file, 'w') as f:
            json.dump(self.conversations, f, indent=2, default=str)
    
    def start_conversation(self, agents):
        """Start monitoring a new conversation."""
        self.current_conversation = {
            "id": f"conv_{datetime.now().isoformat()}",
            "start_time": datetime.now().isoformat(),
            "agents": agents,
            "messages": [],
            "file_operations": [],
            "status": "active"
        }
        self.conversations.append(self.current_conversation)
        return self.current_conversation["id"]
    
    def add_message(self, agent, content, message_type="message"):
        """Add a message to the current conversation."""
        if self.current_conversation:
            message = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "content": content,
                "type": message_type
            }
            self.current_conversation["messages"].append(message)
            self.save_conversations()
            
            # Emit to connected clients
            socketio.emit('new_message', message)
            
            return message
    
    def end_conversation(self):
        """End the current conversation."""
        if self.current_conversation:
            self.current_conversation["end_time"] = datetime.now().isoformat()
            self.current_conversation["status"] = "completed"
            self.save_conversations()

monitor = ConversationMonitor()

# Routes
@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/conversations')
def get_conversations():
    """Get all conversations."""
    return jsonify(monitor.conversations)

@app.route('/api/conversations/<conv_id>')
def get_conversation(conv_id):
    """Get a specific conversation."""
    for conv in monitor.conversations:
        if conv["id"] == conv_id:
            return jsonify(conv)
    return jsonify({"error": "Conversation not found"}), 404

@app.route('/api/file-operations')
def get_file_operations():
    """Get recent file operations."""
    operations = file_logger.get_recent_operations(limit=50)
    return jsonify(operations)

@app.route('/api/active-agents')
def get_active_agents():
    """Get currently active agents."""
    return jsonify(active_agents)

@app.route('/api/rollback/<op_id>', methods=['POST'])
def rollback_operation(op_id):
    """Rollback a file operation."""
    success = file_logger.rollback(op_id)
    return jsonify({"success": success})

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    stats = {
        "total_conversations": len(monitor.conversations),
        "active_conversations": len([c for c in monitor.conversations if c["status"] == "active"]),
        "total_messages": sum(len(c["messages"]) for c in monitor.conversations),
        "total_file_operations": len(file_logger.operations),
        "recent_operations": file_logger.get_recent_operations(limit=5)
    }
    return jsonify(stats)

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'data': 'Connected to dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_update')
def handle_update_request():
    """Handle request for current state update."""
    emit('state_update', {
        'conversations': monitor.conversations[-10:],  # Last 10 conversations
        'file_operations': file_logger.get_recent_operations(limit=20),
        'active_agents': active_agents
    })

# API for AutoGen integration
def log_agent_message(agent_name, message, message_type="message"):
    """Log a message from an AutoGen agent."""
    if not monitor.current_conversation:
        monitor.start_conversation([agent_name])
    
    monitor.add_message(agent_name, message, message_type)
    
    # Also add to conversation log
    conversation_log.append({
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "message": message,
        "type": message_type
    })

def update_agent_status(agent_name, status):
    """Update an agent's status."""
    active_agents[agent_name] = {
        "status": status,
        "last_update": datetime.now().isoformat()
    }
    socketio.emit('agent_status_update', {
        "agent": agent_name,
        "status": status
    })

# Create templates directory and HTML template
def create_dashboard_template():
    """Create the dashboard HTML template."""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoGen + Claude Code Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .container {
            display: grid;
            grid-template-columns: 300px 1fr 300px;
            gap: 1rem;
            padding: 1rem;
            height: calc(100vh - 70px);
        }
        
        .panel {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        
        .panel h2 {
            margin-bottom: 1rem;
            color: #2c3e50;
            font-size: 1.2rem;
        }
        
        .conversation-list {
            list-style: none;
        }
        
        .conversation-item {
            padding: 0.8rem;
            margin-bottom: 0.5rem;
            background: #f8f9fa;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .conversation-item:hover {
            background: #e9ecef;
        }
        
        .conversation-item.active {
            background: #3498db;
            color: white;
        }
        
        .message {
            margin-bottom: 1rem;
            padding: 0.8rem;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }
        
        .message.claude {
            border-left-color: #e74c3c;
        }
        
        .message.system {
            border-left-color: #95a5a6;
            background: #ecf0f1;
        }
        
        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: #7f8c8d;
        }
        
        .message-content {
            white-space: pre-wrap;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.9rem;
        }
        
        .file-operation {
            padding: 0.6rem;
            margin-bottom: 0.4rem;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .file-operation.create {
            border-left: 3px solid #27ae60;
        }
        
        .file-operation.modify {
            border-left: 3px solid #f39c12;
        }
        
        .file-operation.delete {
            border-left: 3px solid #e74c3c;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #3498db;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #7f8c8d;
        }
        
        .agent-status {
            padding: 0.5rem;
            margin-bottom: 0.3rem;
            background: #f8f9fa;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #95a5a6;
        }
        
        .status-indicator.active {
            background: #27ae60;
        }
        
        .rollback-btn {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .rollback-btn:hover {
            background: #c0392b;
        }
        
        #messageContainer {
            max-height: calc(100vh - 200px);
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AutoGen + Claude Code Dashboard</h1>
    </div>
    
    <div class="container">
        <!-- Left Panel: Conversations -->
        <div class="panel">
            <h2>Conversations</h2>
            <ul class="conversation-list" id="conversationList">
                <!-- Populated by JavaScript -->
            </ul>
        </div>
        
        <!-- Center Panel: Messages -->
        <div class="panel">
            <h2>Messages</h2>
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalMessages">0</div>
                    <div class="stat-label">Total Messages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="activeConversations">0</div>
                    <div class="stat-label">Active Conversations</div>
                </div>
            </div>
            <div id="messageContainer">
                <!-- Messages will be displayed here -->
            </div>
        </div>
        
        <!-- Right Panel: File Operations & Agents -->
        <div class="panel">
            <h2>Active Agents</h2>
            <div id="agentList">
                <!-- Agent status will be displayed here -->
            </div>
            
            <h2 style="margin-top: 2rem;">Recent File Operations</h2>
            <div id="fileOperations">
                <!-- File operations will be displayed here -->
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let currentConversation = null;
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to dashboard');
            socket.emit('request_update');
        });
        
        socket.on('new_message', function(message) {
            if (currentConversation) {
                displayMessage(message);
            }
            updateStats();
        });
        
        socket.on('agent_status_update', function(data) {
            updateAgentStatus(data.agent, data.status);
        });
        
        socket.on('state_update', function(data) {
            updateConversationList(data.conversations);
            updateFileOperations(data.file_operations);
            updateAgentList(data.active_agents);
        });
        
        // Functions
        function updateConversationList(conversations) {
            const list = document.getElementById('conversationList');
            list.innerHTML = '';
            
            conversations.forEach(conv => {
                const item = document.createElement('li');
                item.className = 'conversation-item';
                item.innerHTML = `
                    <div><strong>ID:</strong> ${conv.id.substring(5, 15)}...</div>
                    <div><strong>Status:</strong> ${conv.status}</div>
                    <div><strong>Messages:</strong> ${conv.messages.length}</div>
                `;
                item.onclick = () => loadConversation(conv.id);
                list.appendChild(item);
            });
        }
        
        function loadConversation(convId) {
            fetch(`/api/conversations/${convId}`)
                .then(res => res.json())
                .then(conv => {
                    currentConversation = conv;
                    displayConversation(conv);
                });
        }
        
        function displayConversation(conv) {
            const container = document.getElementById('messageContainer');
            container.innerHTML = '';
            
            conv.messages.forEach(msg => displayMessage(msg));
        }
        
        function displayMessage(message) {
            const container = document.getElementById('messageContainer');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${message.agent.toLowerCase()}`;
            
            msgDiv.innerHTML = `
                <div class="message-header">
                    <strong>${message.agent}</strong>
                    <span>${new Date(message.timestamp).toLocaleTimeString()}</span>
                </div>
                <div class="message-content">${escapeHtml(message.content)}</div>
            `;
            
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function updateFileOperations(operations) {
            const container = document.getElementById('fileOperations');
            container.innerHTML = '';
            
            operations.forEach(op => {
                const opDiv = document.createElement('div');
                opDiv.className = `file-operation ${op.type}`;
                
                const filepath = op.filepath.split('/').pop();
                opDiv.innerHTML = `
                    <div><strong>${op.type.toUpperCase()}</strong>: ${filepath}</div>
                    <div style="font-size: 0.8rem; color: #7f8c8d;">${new Date(op.timestamp).toLocaleString()}</div>
                    ${!op.rolled_back ? `<button class="rollback-btn" onclick="rollback('${op.id}')">Rollback</button>` : '<span style="color: #7f8c8d;">Rolled back</span>'}
                `;
                
                container.appendChild(opDiv);
            });
        }
        
        function updateAgentList(agents) {
            const container = document.getElementById('agentList');
            container.innerHTML = '';
            
            Object.entries(agents).forEach(([name, info]) => {
                const agentDiv = document.createElement('div');
                agentDiv.className = 'agent-status';
                
                agentDiv.innerHTML = `
                    <span>${name}</span>
                    <div class="status-indicator ${info.status === 'active' ? 'active' : ''}"></div>
                `;
                
                container.appendChild(agentDiv);
            });
        }
        
        function updateStats() {
            fetch('/api/stats')
                .then(res => res.json())
                .then(stats => {
                    document.getElementById('totalMessages').textContent = stats.total_messages;
                    document.getElementById('activeConversations').textContent = stats.active_conversations;
                });
        }
        
        function rollback(opId) {
            if (confirm('Are you sure you want to rollback this operation?')) {
                fetch(`/api/rollback/${opId}`, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            alert('Operation rolled back successfully');
                            socket.emit('request_update');
                        } else {
                            alert('Failed to rollback operation');
                        }
                    });
            }
        }
        
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }
        
        // Initial load
        updateStats();
        fetch('/api/conversations')
            .then(res => res.json())
            .then(conversations => updateConversationList(conversations.slice(-10)));
    </script>
</body>
</html>'''
    
    with open(templates_dir / "dashboard.html", 'w') as f:
        f.write(dashboard_html)

# Create the template on import
create_dashboard_template()

# AutoGen integration helper
class DashboardIntegration:
    """Helper class for integrating with AutoGen."""
    
    @staticmethod
    def create_monitored_agent(agent_class, *args, **kwargs):
        """Create an AutoGen agent with monitoring capabilities."""
        # This would wrap the AutoGen agent to log messages
        # Implementation depends on AutoGen's specific API
        pass

if __name__ == "__main__":
    print("Starting AutoGen + Claude Code Dashboard...")
    print("Dashboard available at http://localhost:5000")
    socketio.run(app, debug=True, port=5000)