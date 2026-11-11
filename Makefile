.PHONY: help setup train-demo backend frontend test build up
help:
	@echo "make setup       install backend + frontend dependencies"
	@echo "make train-demo  train the SYNTHETIC demo model (pipeline check only)"
	@echo "make backend     run API on :8000        make frontend  run UI on :5173"
	@echo "make test        run backend tests       make build     build the frontend"
	@echo "make up          docker compose up --build"
setup:
	cd backend && python -m pip install -r requirements-dev.txt && cd ../frontend && npm install
train-demo:
	cd backend && python -m training.train --source synthetic --n 2400 --out models --reports reports --activate
backend:
	cd backend && python -m uvicorn app.main:app --reload --port 8000
frontend:
	cd frontend && npm run dev
test:
	cd backend && python -m pytest -q
build:
	cd frontend && npm run build
up:
	docker compose up --build
