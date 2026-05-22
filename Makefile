.PHONY: help dev prod build clean install

help:
	@echo "PASP Control Center - Available Commands"
	@echo ""
	@echo "  make dev       - Start development environment"
	@echo "  make prod      - Start production environment"
	@echo "  make build     - Build Docker images"
	@echo "  make clean     - Stop and remove containers"
	@echo "  make install   - Install dependencies locally"
	@echo "  make backend   - Run backend locally"
	@echo "  make frontend  - Run frontend locally"

dev:
	docker-compose -f docker-compose.dev.yml up --build

prod:
	docker-compose up -d --build

build:
	docker-compose build

clean:
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev
