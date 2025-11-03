#!/bin/bash
# Test runner script for the FastAPI application

echo "Running FastAPI tests..."
echo "========================"

# Activate virtual environment and run tests with coverage
source .venv/bin/activate
python -m pytest tests/ --cov=src --cov-report=term-missing -v

echo ""
echo "Test run complete!"