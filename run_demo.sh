#!/bin/bash

echo "AutoGen + Claude Code Demo Runner"
echo "================================="
echo ""
echo "1) Test Dashboard (no API key needed)"
echo "2) Simple Claude Demo"
echo "3) Full AutoGen + Claude"
echo "4) AutoGen + Claude with Dashboard"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo "Starting dashboard test..."
        python test_dashboard.py
        ;;
    2)
        echo "Running Claude demo..."
        python claude_working_demo.py
        ;;
    3)
        echo "Running AutoGen + Claude..."
        python autogen_claude_final.py
        ;;
    4)
        echo "Running full integration with dashboard..."
        python autogen_with_dashboard.py
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac