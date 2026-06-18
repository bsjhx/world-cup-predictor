.PHONY: help predict batch list-teams update-results test clean install

# Default target - show help
help:
	@echo "World Cup 2026 Predictor - Available Commands"
	@echo ""
	@echo "Usage: make <command> ARGS='arguments'"
	@echo ""
	@echo "Commands:"
	@echo "  make predict ARGS='Brazil Argentina'              - Predict single match"
	@echo "  make predict ARGS='Brazil Argentina -c \"Final\"'   - Predict with context"
	@echo "  make batch ARGS='49300'                           - Batch predict up to ID"
	@echo "  make list-teams                                   - List all valid teams"
	@echo "  make update-results ARGS='data/updated.csv'       - Update results from file"
	@echo "  make test                                         - Run test suite"
	@echo ""
	@echo "Examples:"
	@echo "  make predict ARGS='\"United States\" Mexico -c \"Home advantage\"'"
	@echo "  make batch ARGS='49300 -o custom.csv'"
	@echo ""
	@echo "Development:"
	@echo "  make install                                      - Install dependencies"
	@echo "  make clean                                        - Clean cache files"

# Run single match prediction
predict:
	python -m src.main predict $(ARGS)

# Run batch predictions
batch:
	python -m src.main batch $(ARGS)

# List all teams
list-teams:
	python -m src.main list-teams

# Update match results
update-results:
	python -m src.main update-results $(ARGS)

# Run test suite
test:
	python test/test_predictions.py

# Install dependencies
install:
	pip install -r requirements.txt

# Clean Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "✓ Cleaned cache files"
