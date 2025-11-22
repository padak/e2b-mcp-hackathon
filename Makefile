.PHONY: test test-fast test-slow test-all lint clean

# Run fast tests only (no API calls)
test:
	.venv/bin/pytest -v --tb=short -m "not slow"

# Alias for test
test-fast: test

# Run slow tests (requires API keys)
test-slow:
	.venv/bin/pytest -v --tb=short -m "slow"

# Run all tests
test-all:
	.venv/bin/pytest -v --tb=short

# Run specific test file
test-%:
	.venv/bin/pytest tests/test_$*.py -v --tb=short

# Install dependencies
install:
	pip install -r requirements.txt

# Clean cache
clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
