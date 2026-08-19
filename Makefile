# Enterprise AI Platform - Makefile
# Usage: make <target>

.PHONY: help install install-dev test test-cov lint format clean run run-backend run-frontend docker-build docker-up docker-down migrate seed backup restore logs

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)Enterprise AI Platform - Available Commands$(NC)"
	@echo "=================================================="
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make venv          - Create virtual environment"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make run           - Run backend and frontend (parallel)"
	@echo "  make run-backend   - Run FastAPI backend only"
	@echo "  make run-frontend  - Run Streamlit frontend only"
	@echo "  make dev           - Run with auto-reload"
	@echo ""
	@echo "$(YELLOW)Testing:$(NC)"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-int      - Run integration tests only"
	@echo "  make test-e2e      - Run end-to-end tests"
	@echo ""
	@echo "$(YELLOW)Code Quality:$(NC)"
	@echo "  make lint          - Run linters (ruff, mypy)"
	@echo "  make format        - Format code with black and isort"
	@echo "  make check         - Run all code quality checks"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@echo "  make migrate       - Run database migrations"
	@echo "  make migrate-new   - Create new migration (MSG='description')"
	@echo "  make seed          - Seed database with sample data"
	@echo "  make backup        - Create database backup"
	@echo "  make restore FILE= - Restore database from backup"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@echo "  make clean         - Remove Python cache files"
	@echo "  make clean-all     - Remove cache, venv, and data"
	@echo "  make clean-data    - Remove data files (database, logs)"

# ==================== Setup ====================

venv:
	@echo "$(YELLOW)Creating virtual environment...$(NC)"
	python3 -m venv .venv
	@echo "$(GREEN)Virtual environment created. Run: source .venv/bin/activate$(NC)"

install:
	@echo "$(YELLOW)Installing production dependencies...$(NC)"
	pip install --upgrade pip
	pip install -r requirements/base.txt

install-dev: install
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	pip install -r requirements/dev.txt
	pip install -r requirements/test.txt
	pre-commit install

# ==================== Development ====================

run:
	@echo "$(YELLOW)Starting backend and frontend...$(NC)"
	@trap 'kill 0' EXIT; \
	(make run-backend &) \
	(make run-frontend &) \
	wait

run-backend:
	@echo "$(GREEN)Starting FastAPI backend on http://localhost:8000$(NC)"
	uvicorn src.presentation.api:create_app --factory --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "$(GREEN)Starting Streamlit frontend on http://localhost:8501$(NC)"
	streamlit run src/presentation/web/Home.py

dev:
	@echo "$(YELLOW)Starting in development mode with auto-reload...$(NC)"
	ENVIRONMENT=development DEBUG=true make run

# ==================== Testing ====================

test:
	@echo "$(YELLOW)Running all tests...$(NC)"
	pytest tests/ -v

test-cov:
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-unit:
	@echo "$(YELLOW)Running unit tests...$(NC)"
	pytest tests/unit/ -v

test-int:
	@echo "$(YELLOW)Running integration tests...$(NC)"
	pytest tests/integration/ -v

test-e2e:
	@echo "$(YELLOW)Running end-to-end tests...$(NC)"
	pytest tests/e2e/ -v

# ==================== Code Quality ====================

lint:
	@echo "$(YELLOW)Running linters...$(NC)"
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	@echo "$(YELLOW)Formatting code...$(NC)"
	black src/ tests/
	isort src/ tests/
	ruff check --fix src/ tests/

check: lint
	@echo "$(GREEN)All checks passed!$(NC)"

# ==================== Database ====================

migrate:
	@echo "$(YELLOW)Running database migrations...$(NC)"
	cd data/database/migrations && alembic upgrade head

migrate-new:
	@echo "$(YELLOW)Creating new migration...$(NC)"
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: MSG variable not set. Usage: make migrate-new MSG='description'$(NC)"; \
		exit 1; \
	fi
	cd data/database/migrations && alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	@echo "$(YELLOW)Rolling back migration...$(NC)"
	cd data/database/migrations && alembic downgrade -1

seed:
	@echo "$(YELLOW)Seeding database with sample data...$(NC)"
	python scripts/seed_data.py

backup:
	@echo "$(YELLOW)Creating database backup...$(NC)"
	python scripts/backup.py

restore:
	@echo "$(YELLOW)Restoring database from backup...$(NC)"
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: FILE variable not set. Usage: make restore FILE=backup.db$(NC)"; \
		exit 1; \
	fi
	python scripts/restore.py $(FILE)

# ==================== Docker ====================

docker-build:
	@echo "$(YELLOW)Building Docker images...$(NC)"
	docker-compose -f deployment/docker/docker-compose.yml build

docker-up:
	@echo "$(YELLOW)Starting Docker containers...$(NC)"
	docker-compose -f deployment/docker/docker-compose.yml up -d
	@echo "$(GREEN)Services started:$(NC)"
	@echo "  - Frontend: http://localhost:8501"
	@echo "  - Backend: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/api/docs"

docker-down:
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	docker-compose -f deployment/docker/docker-compose.yml down

docker-logs:
	docker-compose -f deployment/docker/docker-compose.yml logs -f

docker-shell-backend:
	docker exec -it aiplatform-backend-1 /bin/bash

docker-shell-frontend:
	docker exec -it aiplatform-frontend-1 /bin/bash

# ==================== Cleanup ====================

clean:
	@echo "$(YELLOW)Cleaning Python cache files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-data:
	@echo "$(RED)WARNING: This will delete all data files!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/database/*.db data/vector_store/* data/generated/*/* data/logs/*.log; \
		echo "$(GREEN)Data files removed$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

clean-all: clean
	@echo "$(RED)WARNING: This will delete virtual environment and all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf .venv/; \
		rm -rf data/; \
		echo "$(GREEN)Full cleanup complete!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# ==================== Utilities ====================

logs:
	@echo "$(YELLOW)Tailing application logs...$(NC)"
	tail -f data/logs/app.log

health:
	@echo "$(YELLOW)Checking service health...$(NC)"
	@curl -s http://localhost:8000/api/health | jq . || echo "$(RED)Backend not responding$(NC)"
	@curl -s http://localhost:8501/_stcore/health | jq . || echo "$(RED)Frontend not responding$(NC)"

init:
	@echo "$(YELLOW)Initializing project...$(NC)"
	python scripts/init_data_directories.py
	cp .env.example .env
	@echo "$(GREEN)Project initialized! Edit .env with your configuration.$(NC)"