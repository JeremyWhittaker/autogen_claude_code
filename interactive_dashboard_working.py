#!/usr/bin/env python3
"""
Interactive Web Dashboard for AutoGen + Claude Code.
Working version with proper function registration.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
import threading
import queue
import time
from datetime import datetime
from pathlib import Path
import logging
import sys
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AutoGen components
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("WARNING: AutoGen not available. Chat functionality will be limited.")

# Import our components
try:
    from claude_working_demo import claude_execute
    from file_operation_logger import FileOperationLogger
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("WARNING: Claude components not available.")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('interactive_dashboard_working.log')
    ]
)
logger = logging.getLogger("dashboard")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-secret-key'

# Enable CORS for all origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO with proper settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    allow_unsafe_werkzeug=True
)

# Initialize components
file_logger = FileOperationLogger() if CLAUDE_AVAILABLE else None
message_queue = queue.Queue()
agent_responses = queue.Queue()

# Global variables for agents
orchestrator = None
code_executor = None
conversation_active = False
current_session_id = None

def get_server_info():
    """Get comprehensive server information"""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Get all IPs
    all_ips = []
    try:
        result = socket.getaddrinfo(hostname, None)
        for item in result:
            ip = item[4][0]
            if ip not in all_ips and ':' not in ip:  # IPv4 only
                all_ips.append(ip)
    except:
        all_ips = [local_ip]
    
    return {
        'hostname': hostname,
        'primary_ip': local_ip,
        'all_ips': all_ips,
        'port': 5000
    }

def init_agents():
    """Initialize AutoGen agents with proper function registration"""
    global orchestrator, code_executor
    
    if not AUTOGEN_AVAILABLE:
        logger.error("AutoGen not available")
        return False
    
    try:
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your-openai-api-key-here":
            logger.error("Valid OpenAI API key not found in environment")
            return False
        
        logger.info(f"Initializing AutoGen with API key: {api_key[:10]}...")
        
        # LLM configuration
        config_list = [{
            "model": "gpt-4o-mini",
            "api_key": api_key
        }]
        
        llm_config = {
            "config_list": config_list,
            "temperature": 0.7,
            "functions": [
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
        }
        
        # Create orchestrator agent
        orchestrator = AssistantAgent(
            name="Orchestrator",
            llm_config=llm_config,
            system_message="""You are an AI orchestrator that helps users with coding tasks.
            When users ask you to write code, use the claude_execute function to generate code.
            Always call the function with a clear prompt that includes 'Show me the complete code'.
            """
        )
        
        # Create code executor agent  
        code_executor = UserProxyAgent(
            name="CodeExecutor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": "./generated_code",
                "use_docker": False
            }
        )
        
        # Register the function properly
        def claude_execute_wrapper(prompt: str) -> str:
            """Wrapper for claude_execute that ensures proper return format"""
            logger.info(f"Claude execute called with prompt: {prompt[:100]}...")
            try:
                result = claude_execute(prompt)
                logger.info(f"Claude returned: {result[:200]}...")
                return result
            except Exception as e:
                logger.error(f"Error in claude_execute: {e}")
                return f"Error calling Claude: {str(e)}"
        
        # Register function with executor
        code_executor.register_function(
            function_map={
                "claude_execute": claude_execute_wrapper
            }
        )
        
        logger.info("Agents initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

@app.route('/')
def index():
    """Serve the dashboard"""
    server_info = get_server_info()
    logger.info(f"Dashboard accessed from {request.remote_addr}")
    logger.info(f"Server info: {server_info}")
    return render_template('interactive_dashboard.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'autogen_available': AUTOGEN_AVAILABLE,
        'claude_available': CLAUDE_AVAILABLE,
        'agents_initialized': orchestrator is not None,
        'server_info': get_server_info()
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        client_id = request.sid
        client_ip = request.remote_addr
        
        logger.info(f"Client connected: {client_id} from {client_ip}")
        
        # Send connection confirmation
        emit('connected', {
            'status': 'connected',
            'session_id': client_id,
            'autogen_available': AUTOGEN_AVAILABLE,
            'claude_available': CLAUDE_AVAILABLE
        })
        
        # Try to initialize agents if not done
        if orchestrator is None and AUTOGEN_AVAILABLE:
            emit('system_message', {
                'message': 'Initializing AI agents...',
                'type': 'info'
            })
            
            if init_agents():
                emit('system_message', {
                    'message': 'AI agents initialized successfully!',
                    'type': 'success'
                })
                emit('agents_ready', {'ready': True})
            else:
                emit('system_message', {
                    'message': 'Failed to initialize agents. Please check your API key in the .env file.',
                    'type': 'error'
                })
                emit('agents_ready', {'ready': False})
        
    except Exception as e:
        logger.error(f"Error in connect handler: {e}")
        import traceback
        logger.error(traceback.format_exc())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('start_session')
def handle_start_session(data):
    """Start a new chat session"""
    global current_session_id, conversation_active
    
    try:
        current_session_id = data.get('session_id', datetime.now().strftime('%Y%m%d_%H%M%S'))
        conversation_active = True
        
        logger.info(f"Started session: {current_session_id}")
        
        emit('session_started', {
            'session_id': current_session_id,
            'timestamp': datetime.now().isoformat()
        })
        
        if orchestrator is None:
            emit('system_message', {
                'message': 'Agents not initialized. Please refresh and try again.',
                'type': 'error'
            })
            
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        emit('error', {'message': str(e)})

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming message from user"""
    try:
        message = data.get('message', '')
        logger.info(f"Received message: {message}")
        
        if not orchestrator:
            emit('agent_message', {
                'agent': 'System',
                'message': 'Agents not initialized. Please check your OpenAI API key.',
                'type': 'error',
                'timestamp': datetime.now().isoformat()
            })
            return
        
        # Emit user message
        emit('agent_message', {
            'agent': 'User', 
            'message': message,
            'type': 'user',
            'timestamp': datetime.now().isoformat()
        }, broadcast=True)
        
        # Process with AutoGen in a thread
        def process_with_autogen():
            try:
                logger.info("Starting AutoGen conversation...")
                
                # Create a list to capture conversation history
                conversation_history = []
                
                # Custom print to capture output
                output_buffer = []
                original_print = print
                
                def capture_print(*args, **kwargs):
                    output = ' '.join(str(arg) for arg in args)
                    output_buffer.append(output)
                    
                    # Parse the output to determine the agent
                    if output.strip():
                        # Emit each line of output
                        for line in output.split('\n'):
                            if line.strip():
                                # Determine agent from output
                                agent = 'System'
                                if 'Orchestrator' in line:
                                    agent = 'Orchestrator'
                                elif 'CodeExecutor' in line:
                                    agent = 'CodeExecutor'
                                elif '>>>>>>>> USING AUTO REPLY...' in line:
                                    agent = 'System'
                                elif '>>>>>>>> EXECUTING FUNCTION' in line:
                                    agent = 'System'
                                elif 'claude' in line.lower():
                                    agent = 'Claude'
                                
                                # Clean up the message
                                clean_message = line
                                if ' (to ' in line and '):\n' in line:
                                    # Extract just the agent name and remove the "(to X):" part
                                    parts = line.split(' (to ')
                                    if len(parts) > 0:
                                        agent = parts[0].strip()
                                        if '):\n' in parts[1]:
                                            clean_message = ''
                                elif line.startswith('Orchestrator (to CodeExecutor):'):
                                    agent = 'Orchestrator'
                                    clean_message = line.replace('Orchestrator (to CodeExecutor):', '').strip()
                                elif line.startswith('CodeExecutor (to Orchestrator):'):
                                    agent = 'CodeExecutor'
                                    clean_message = line.replace('CodeExecutor (to Orchestrator):', '').strip()
                                
                                if clean_message and not clean_message.startswith('------'):
                                    socketio.emit('agent_message', {
                                        'agent': agent,
                                        'message': clean_message,
                                        'type': 'assistant',
                                        'timestamp': datetime.now().isoformat()
                                    })
                    
                    original_print(*args, **kwargs)
                
                # Monkey patch print
                import builtins
                builtins.print = capture_print
                
                try:
                    # Initiate chat
                    code_executor.initiate_chat(
                        orchestrator,
                        message=message,
                        clear_history=False
                    )
                    
                    logger.info("AutoGen conversation completed successfully")
                    
                except Exception as e:
                    logger.error(f"Error during AutoGen conversation: {e}")
                    error_msg = str(e)
                    
                    # Check for specific error patterns
                    if "tool_call_id" in error_msg:
                        socketio.emit('agent_message', {
                            'agent': 'System',
                            'message': 'There was an error with the function call. Please try rephrasing your request.',
                            'type': 'error',
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        socketio.emit('agent_message', {
                            'agent': 'System',
                            'message': f'Error: {error_msg}',
                            'type': 'error',
                            'timestamp': datetime.now().isoformat()
                        })
                
                finally:
                    # Restore print
                    builtins.print = original_print
                
            except Exception as e:
                logger.error(f"Error in AutoGen processing: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                socketio.emit('agent_message', {
                    'agent': 'System',
                    'message': f'Error: {str(e)}',
                    'type': 'error', 
                    'timestamp': datetime.now().isoformat()
                })
        
        # Start processing thread
        thread = threading.Thread(target=process_with_autogen)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        emit('error', {'message': str(e)})

@socketio.on('ping')
def handle_ping():
    """Handle ping for connection testing"""
    emit('pong', {'timestamp': datetime.now().isoformat()})

# Create template if it doesn't exist
template_dir = Path('templates')
template_dir.mkdir(exist_ok=True)

# The template is the same as in interactive_dashboard_fixed.py
# (template code omitted for brevity - use the same template)

if __name__ == '__main__':
    server_info = get_server_info()
    
    print("\n" + "="*60)
    print("🚀 AUTOGEN + CLAUDE INTERACTIVE DASHBOARD (WORKING)")
    print("="*60)
    print(f"Server starting on all network interfaces...")
    print(f"\nAccess the dashboard at:")
    print(f"  - http://localhost:5000")
    for ip in server_info['all_ips']:
        print(f"  - http://{ip}:5000")
    print(f"\nDebug log: interactive_dashboard_working.log")
    print("\n⚠️  IMPORTANT: Make sure to set your OpenAI API key in the .env file!")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Create generated_code directory if it doesn't exist
    Path("./generated_code").mkdir(exist_ok=True)
    
    try:
        # Run with explicit host binding to all interfaces
        socketio.run(
            app, 
            host='0.0.0.0',  # Bind to all interfaces
            port=5000,
            debug=True,
            allow_unsafe_werkzeug=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        logger.error(traceback.format_exc())