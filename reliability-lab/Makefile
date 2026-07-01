.PHONY: install run test lint compose-up compose-down

install:
	python -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

test:
	pytest

lint:
	ruff check .

compose-up:
	docker compose -f infra/docker/docker-compose.yml up --build

compose-down:
	docker compose -f infra/docker/docker-compose.yml down

