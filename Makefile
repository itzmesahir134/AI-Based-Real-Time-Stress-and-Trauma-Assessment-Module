.PHONY: help install lint format test test-unit test-cov docker-up docker-down docker-logs infra-up infra-down migrate migrate-new migrate-down up down logs generate-types clean

help:
	@echo "SAATHI-AI — Development Commands"
	@echo ""
	@echo "  make install         Install core & dev Python dependencies"
	@echo "  make lint            Run Ruff linter and mypy type checks"
	@echo "  make format          Auto-format code with Ruff"
	@echo "  make test            Run all test suites"
	@echo "  make test-unit       Run unit tests only (fast)"
	@echo "  make test-cov        Run tests with HTML & terminal coverage"
	@echo "  make infra-up        Start core backing infra (Postgres, Redis, MinIO)"
	@echo "  make infra-down      Stop core backing infra"
	@echo "  make migrate         Run Alembic migrations to head"
	@echo "  make migrate-new     Generate new Alembic migration (usage: make migrate-new MSG='desc')"
	@echo "  make migrate-down    Rollback last Alembic migration"
	@echo "  make up              Build & start full stack (infra, migrate, api, worker)"
	@echo "  make down            Stop full stack and remove volumes"
	@echo "  make logs            Tail API and worker container logs"
	@echo "  make generate-types  Generate TypeScript types from FastAPI OpenAPI schemas"
	@echo "  make clean           Clean up caches and temporary test/build artifacts"

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev,test]"

lint:
	ruff check .
	mypy services/ packages/

format:
	ruff check --fix .
	ruff format .

test:
	pytest tests/

test-unit:
	pytest tests/ -m unit

test-cov:
	pytest tests/ --cov=services --cov=packages --cov-report=term-missing --cov-report=html

# --- Infrastructure ---
infra-up:
	docker compose -f infra/compose/docker-compose.yml up -d postgres redis minio

infra-down:
	docker compose -f infra/compose/docker-compose.yml down

# Backwards-compatible aliases
docker-up: infra-up
docker-down: infra-down
docker-logs:
	docker compose -f infra/compose/docker-compose.yml logs -f

# --- Migrations ---
migrate:
	alembic -c infra/migrations/alembic.ini upgrade head

migrate-new:
	alembic -c infra/migrations/alembic.ini revision --autogenerate -m "$(MSG)"

migrate-down:
	alembic -c infra/migrations/alembic.ini downgrade -1

# --- Full stack ---
up:
	docker compose -f infra/compose/docker-compose.yml up --build -d

down:
	docker compose -f infra/compose/docker-compose.yml down -v

logs:
	docker compose -f infra/compose/docker-compose.yml logs -f api worker

generate-types:
	datamodel-codegen --url http://localhost:8000/openapi.json --output apps/web/src/types/api.ts --target-python-version 3.12

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.mypy_cache')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.ruff_cache')]"
