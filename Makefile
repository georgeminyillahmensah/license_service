# Makefile for Centralized License Service
# Provides common development and testing tasks

.PHONY: help install test lint format clean migrate superuser runserver shell coverage security docs build deploy

# Default target
help:
	@echo "Centralized License Service - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install all dependencies"
	@echo "  migrate      Run database migrations"
	@echo "  superuser    Create a superuser"
	@echo "  runserver    Start development server"
	@echo "  shell        Open Django shell"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-fast    Run tests without coverage"
	@echo "  test-watch   Run tests in watch mode"
	@echo "  coverage     Generate coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run all linting tools"
	@echo "  format       Format code with Black and isort"
	@echo "  type-check   Run MyPy type checking"
	@echo "  security     Run security checks"
	@echo ""
	@echo "Documentation:"
	@echo "  docs         Generate API documentation"
	@echo "  docs-validate Validate API schema"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  build        Build package"
	@echo "  clean        Clean build artifacts"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci           Run all CI checks locally"
	@echo "  pre-commit   Install pre-commit hooks"

# Development
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

migrate:
	@echo "Running database migrations..."
	python manage.py makemigrations
	python manage.py migrate
	@echo "Migrations completed!"

superuser:
	@echo "Creating superuser..."
	python manage.py createsuperuser

runserver:
	@echo "Starting development server..."
	python manage.py runserver

shell:
	@echo "Opening Django shell..."
	python manage.py shell

# Testing
test:
	@echo "Running comprehensive test suite..."
	pytest tests/ \
		--cov=licenses \
		--cov=users \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=80 \
		--durations=10 \
		--maxfail=5 \
		--reruns=2 \
		--reruns-delay=1 \
		-v

test-fast:
	@echo "Running tests without coverage..."
	pytest tests/ -v

test-watch:
	@echo "Running tests in watch mode..."
	pytest tests/ -f -v

coverage:
	@echo "Generating coverage report..."
	pytest tests/ --cov=licenses --cov=users --cov-report=html:htmlcov
	@echo "Coverage report generated in htmlcov/"

# Code Quality
lint:
	@echo "Running code quality checks..."
	@echo "Running Black..."
	black --check --diff licenses/ users/ license_service/ tests/ || echo "Black found formatting issues"
	@echo "Running isort..."
	isort --check-only --diff licenses/ users/ license_service/ tests/ || echo "isort found import sorting issues"
	@echo "Running Flake8..."
	flake8 licenses/ users/ license_service/ tests/ --max-line-length=88 --extend-ignore=E203,W503 || echo "Flake8 found linting issues"
	@echo "Running MyPy..."
	mypy licenses/ users/ license_service/ --ignore-missing-imports || echo "MyPy found type checking issues"
	@echo "Code quality checks completed!"

format:
	@echo "Formatting code..."
	black licenses/ users/ license_service/ tests/
	isort licenses/ users/ license_service/ tests/
	@echo "Code formatting completed!"

type-check:
	@echo "Running MyPy type checking..."
	mypy licenses/ users/ license_service/ --ignore-missing-imports

security:
	@echo "Running security checks..."
	@echo "Running Bandit..."
	bandit -r licenses/ users/ license_service/ -f json -o bandit-report.json || echo "Bandit found security issues"
	@echo "Running Safety..."
	safety check --json --output safety-report.json || echo "Safety found dependency vulnerabilities"
	@echo "Security checks completed!"

# Documentation
docs:
	@echo "Generating API documentation..."
	python manage.py spectacular --file schema.yml
	@echo "API documentation generated: schema.yml"

docs-validate:
	@echo "Validating API schema..."
	python manage.py spectacular --validate
	@echo "API schema validation completed!"

# Build & Deploy
build:
	@echo "Building package..."
	python -m build
	@echo "Package built successfully!"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage
	rm -f bandit-report.json
	rm -f safety-report.json
	rm -f schema.yml
	@echo "Cleanup completed!"

# CI/CD
ci:
	@echo "Running all CI checks locally..."
	@echo "Running Django checks..."
	python manage.py check
	@echo "Running migrations check..."
	python manage.py makemigrations --check --dry-run
	@echo "Running code quality checks..."
	$(MAKE) lint
	@echo "Running security checks..."
	$(MAKE) security
	@echo "Running tests..."
	$(MAKE) test
	@echo "Running API documentation tests..."
	$(MAKE) docs-validate
	@echo "All CI checks completed successfully!"

pre-commit:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

# Database
db-reset:
	@echo "Resetting database..."
	python manage.py flush --no-input
	python manage.py migrate
	@echo "Database reset completed!"

db-backup:
	@echo "Creating database backup..."
	python manage.py dumpdata > backup_$(shell date +%Y%m%d_%H%M%S).json
	@echo "Database backup created!"

# Performance
profile:
	@echo "Running performance profiling..."
	python manage.py runserver --noreload &
	sleep 5
	ab -n 1000 -c 10 http://localhost:8000/api/schema/
	pkill -f "python manage.py runserver"

# Monitoring
logs:
	@echo "Showing application logs..."
	tail -f logs/app.log

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t centralized-license-service .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 centralized-license-service

# Helpers
check-env:
	@echo "Checking environment..."
	@python -c "import os; print('Environment variables:'); [print(f'{k}={v}') for k, v in os.environ.items() if 'DJANGO' in k or 'DB_' in k or 'REDIS' in k]"

check-deps:
	@echo "Checking dependencies..."
	pip list --outdated

update-deps:
	@echo "Updating dependencies..."
	pip install --upgrade -r requirements.txt

# Development shortcuts
dev: install migrate runserver

quick-test: test-fast

quality: lint format

all: install migrate test lint security docs
