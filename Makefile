.PHONY: help build up down logs restart clean

help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker containers
	docker-compose build

up: ## Start all Docker containers in detached mode
	docker-compose up -d

down: ## Stop and remove all Docker containers
	docker-compose down

logs: ## Follow the logs for all containers
	docker-compose logs -f

restart: down up ## Restart all containers

clean: down ## Remove containers, networks, volumes, and images created by up
	docker-compose down -v --rmi all
