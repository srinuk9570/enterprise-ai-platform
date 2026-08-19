# Makefile for deployment tasks

.PHONY: help build up down logs clean backup restore

help:
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make backup     - Create database backup"
	@echo "  make restore    - Restore database from backup"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-db   - Open database shell"

build:
	docker-compose -f deployment/docker/docker-compose.yml build

up:
	docker-compose -f deployment/docker/docker-compose.yml up -d

down:
	docker-compose -f deployment/docker/docker-compose.yml down

logs:
	docker-compose -f deployment/docker/docker-compose.yml logs -f

clean:
	docker-compose -f deployment/docker/docker-compose.yml down -v
	rm -rf data/database/*.db

backup:
	@docker exec -it aiplatform-backend-1 python scripts/backup.py

restore:
	@docker exec -it aiplatform-backend-1 python scripts/restore.py $(FILE)

shell-backend:
	docker exec -it aiplatform-backend-1 /bin/bash

shell-db:
	docker exec -it aiplatform-backend-1 sqlite3 /app/data/database/app.db

deploy-systemd:
	sudo bash deployment/scripts/deploy.sh

health:
	bash deployment/scripts/health_check.sh

prod-up:
	docker-compose -f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml up -d

prod-down:
	docker-compose -f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml down