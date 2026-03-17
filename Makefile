# =============================================================================
# ApplyFlow — Developer Makefile
# =============================================================================

.PHONY: help setup dev build clean docker-up docker-down migrate seed test lint

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ──────────────────────────────────────────────────────────────────
setup: ## Initial project setup
	@echo "→ Installing Node dependencies..."
	pnpm install
	@echo "→ Setting up Python environment..."
	cd apps/api && poetry install
	cd packages/agent && poetry install
	cd packages/integrations && poetry install
	@echo "→ Copying .env.example to .env..."
	cp -n .env.example .env || true
	@echo "✓ Setup complete! Edit .env with your credentials."

# ─── Development ─────────────────────────────────────────────────────────────
dev: ## Start all dev servers (frontend + backend + infra)
	docker-compose up -d postgres redis
	@echo "→ Waiting for DB..."
	sleep 3
	$(MAKE) migrate
	pnpm dev

dev-api: ## Start only the API in dev mode
	cd apps/api && uvicorn main:app --reload --port 8000

dev-web: ## Start only the Next.js frontend
	cd apps/web && pnpm dev

dev-worker: ## Start Celery worker
	cd apps/api && celery -A app.workers.celery_app worker --loglevel=info

# ─── Database ────────────────────────────────────────────────────────────────
migrate: ## Run Alembic migrations
	cd apps/api && alembic upgrade head

migrate-down: ## Roll back last migration
	cd apps/api && alembic downgrade -1

migrate-create: ## Create a new migration (usage: make migrate-create NAME=my_migration)
	cd apps/api && alembic revision --autogenerate -m "$(NAME)"

seed: ## Seed the database with sample data
	cd apps/api && python scripts/seed.py

db-reset: ## Drop and recreate the database (DANGER: destroys all data)
	cd apps/api && alembic downgrade base && alembic upgrade head && python scripts/seed.py

# ─── Docker ──────────────────────────────────────────────────────────────────
docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-build: ## Rebuild Docker images
	docker-compose build

docker-logs: ## Follow Docker logs
	docker-compose logs -f

docker-ps: ## Show running containers
	docker-compose ps

# ─── Testing ─────────────────────────────────────────────────────────────────
test: ## Run all tests
	cd apps/api && pytest
	pnpm test

test-api: ## Run API tests
	cd apps/api && pytest -v

test-web: ## Run frontend tests
	cd apps/web && pnpm test

# ─── Code Quality ────────────────────────────────────────────────────────────
lint: ## Lint all code
	pnpm lint
	cd apps/api && ruff check .

format: ## Format all code
	pnpm format
	cd apps/api && ruff format .

# ─── Build ───────────────────────────────────────────────────────────────────
build: ## Build all packages and apps
	pnpm build

clean: ## Remove all build artifacts
	pnpm clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
