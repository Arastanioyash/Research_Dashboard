.PHONY: install dev test fmt

install:
	python -m pip install -r backend/requirements-dev.txt

dev:
	docker compose up --build

test:
	cd backend && python -m pytest -q

fmt:
	cd backend && python -m black app tests
