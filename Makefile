.PHONY: help install lint format test test-unit test-cov docker-up docker-down docker-logs generate-types clean

help:
	@echo "SAATHI-AI — Development Commands"
	@echo ""
	@echo "  make install         Install core & dev Python dependencies"
	@echo "  make lint            Run Ruff linter and mypy type checks"
	@echo "  make format          Auto-format code with Ruff"
	@echo "  make test            Run all test suites"
	@echo "  make test-unit       Run unit tests only (fast)"
	@echo "  make test-cov        Run tests with HTML & terminal coverage"
	@echo "  make docker-up       Start infrastructure services (Postgres, Redis, LiveKit)"
	@echo "  make docker-down     Stop infrastructure services"
	@echo "  make docker-logs     Tail infrastructure logs"
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

docker-up:
	docker compose -f infra/compose/docker-compose.yml up -d

docker-down:
	docker compose -f infra/compose/docker-compose.yml down

docker-logs:
	docker compose -f infra/compose/docker-compose.yml logs -f

generate-types:
	datamodel-codegen --url http://localhost:8000/openapi.json --output apps/web/src/types/api.ts --target-python-version 3.12

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.mypy_cache')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.ruff_cache')]"
