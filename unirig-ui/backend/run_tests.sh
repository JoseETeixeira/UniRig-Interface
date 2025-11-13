#!/bin/bash
# Run backend tests with coverage reporting

set -e

echo "====================================="
echo "Running UniRig UI Backend Test Suite"
echo "====================================="
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "ERROR: pytest not installed. Installing test dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Running tests..."
echo ""

# Run tests with coverage
pytest \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing:skip-covered \
    --cov-branch \
    -v \
    "$@"

EXIT_CODE=$?

echo ""
echo "====================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed (exit code: $EXIT_CODE)"
fi
echo "====================================="
echo ""
echo "Coverage report generated at: htmlcov/index.html"
echo "Open with: firefox htmlcov/index.html"
echo ""

exit $EXIT_CODE
