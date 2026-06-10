COMPOSE := docker compose
API_SERVICE := api
WORKER_SERVICE := worker
BEAT_SERVICE := beat
DB_SERVICE := postgres
ALEMBIC_MSG ?= update schema
ALEMBIC_REV ?= -1

.PHONY: help build up down restart ps logs logs-api logs-worker logs-beat logs-db \
	shell-api shell-worker shell-db \
	alembic-init revision upgrade downgrade current history heads scrape-all scrape-due \
	api-url health

help:
	@printf "%s\n" \
		"make build                Build Docker images" \
		"make up                   Start all services in detached mode" \
		"make down                 Stop all services" \
		"make restart              Rebuild and restart all services" \
		"make ps                   Show container status" \
		"make logs                 Tail all service logs" \
		"make logs-api             Tail API logs" \
		"make logs-worker          Tail worker logs" \
		"make logs-beat            Tail beat logs" \
		"make logs-db              Tail Postgres logs" \
		"make shell-api            Open a shell in the API container" \
		"make shell-worker         Open a shell in the worker container" \
		"make shell-db             Open psql in the Postgres container" \
		"make alembic-init         Initialize Alembic in ./migrations" \
		"make revision ALEMBIC_MSG='create jobs table'" \
		"make upgrade              Run alembic upgrade head" \
		"make downgrade ALEMBIC_REV=-1" \
		"make current              Show current Alembic revision" \
		"make history              Show Alembic history" \
		"make heads                Show Alembic heads" \
		"make scrape-all           Queue scrape jobs for all active sources" \
		"make scrape-due           Run due-source scheduling check now" \
		"make api-url              Print local API URL" \
		"make health               Call the health endpoint"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d --build

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-api:
	$(COMPOSE) logs -f $(API_SERVICE)

logs-worker:
	$(COMPOSE) logs -f $(WORKER_SERVICE)

logs-beat:
	$(COMPOSE) logs -f $(BEAT_SERVICE)

logs-db:
	$(COMPOSE) logs -f $(DB_SERVICE)

shell-api:
	$(COMPOSE) exec $(API_SERVICE) sh

shell-worker:
	$(COMPOSE) exec $(WORKER_SERVICE) sh

shell-db:
	$(COMPOSE) exec $(DB_SERVICE) psql -U $$POSTGRES_USER -d $$POSTGRES_DB

alembic-init:
	$(COMPOSE) exec $(API_SERVICE) alembic init migrations

revision:
	$(COMPOSE) exec $(API_SERVICE) alembic revision --autogenerate -m "$(ALEMBIC_MSG)"

upgrade:
	$(COMPOSE) exec $(API_SERVICE) alembic upgrade head

downgrade:
	$(COMPOSE) exec $(API_SERVICE) alembic downgrade $(ALEMBIC_REV)

current:
	$(COMPOSE) exec $(API_SERVICE) alembic current

history:
	$(COMPOSE) exec $(API_SERVICE) alembic history

heads:
	$(COMPOSE) exec $(API_SERVICE) alembic heads

scrape-all:
	$(COMPOSE) exec $(API_SERVICE) python -c "from app.tasks.scraping import scrape_all_sources_task; print(scrape_all_sources_task.delay().id)"

scrape-due:
	$(COMPOSE) exec $(API_SERVICE) python -c "from app.tasks.scraping import scrape_due_sources_task; print(scrape_due_sources_task())"

api-url:
	@printf "http://localhost:%s\n" "$${API_PORT:-8001}"

health:
	curl -fsS "http://localhost:$${API_PORT:-8001}/health"
