#!/bin/bash

# Funding Research Agent - Test Runner

set -e

echo "Funding Research Agent Test Runner"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and add your API keys."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Check for required API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: No LLM API key found!"
    echo "Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
if ! python -c "import funding_researcher" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -e .
fi

# Run the test
echo ""
echo "Running funding research test..."
echo ""

if [ "$1" == "ev" ]; then
    python tests/test_funding_research.py ev
else
    python tests/test_funding_research.py
fi
