.PHONY: help up down backend web mobile test lint

help:
	@echo "FlashPort — Available commands:"
	@echo "  make up       Start full stack (Docker)"
	@echo "  make down     Stop Docker stack"
	@echo "  make backend  Run backend locally (requires venv)"
	@echo "  make web      Run web dashboard locally"
	@echo "  make mobile   Run Flutter app"
	@echo "  make test     Run backend tests"
	@echo "  make lint     Lint backend code"

up:
	docker-compose up --build

down:
	docker-compose down

backend:
	cd backend && venv/bin/uvicorn app.main:app --reload --port 8000

web:
	cd web && node_modules/.bin/vite

mobile:
	cd mobile && flutter run

test:
	cd backend && venv/bin/python -m pytest tests/ -v

lint:
	cd backend && venv/bin/python -m ruff check app/
