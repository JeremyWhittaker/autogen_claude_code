#!/usr/bin/env python3
"""
Quick setup script for AutoGen + Claude Code integration
"""
import os
import subprocess
import sys

def main():
    print("🚀 Setting up AutoGen + Claude Code Integration...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Install requirements
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("\n⚠️  No .env file found!")
        print("📝 Creating .env from template...")
        
        # Copy .env.example to .env
        with open(".env.example", "r") as f:
            template = f.read()
        
        with open(".env", "w") as f:
            f.write(template)
        
        print("\n🔑 Please edit .env and add your API keys:")
        print("   - OPENAI_API_KEY (required)")
        print("   - ANTHROPIC_API_KEY (optional)")
    
    # Check Claude CLI
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
        print("✅ Claude CLI is installed")
    except:
        print("❌ Claude CLI not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "claude"])
    
    print("\n✨ Setup complete!")
    print("\n🎯 Next steps:")
    print("1. Edit .env and add your API keys")
    print("2. Run: python test_final.py")
    print("3. Try: python autogen_claude_final.py")

if __name__ == "__main__":
    main()