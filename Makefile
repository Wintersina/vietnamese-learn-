# Học Tiếng Việt — dev workflow.
# `make setup` bootstraps everything; `make run` starts the app.

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip
PORT ?= 8000

.DEFAULT_GOAL := help

.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

$(VENV):  ## Create the virtualenv
	python3 -m venv $(VENV)

.PHONY: install
install: $(VENV)  ## Install Python dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

.PHONY: migrations
migrations:  ## Create new DB migrations from model changes
	$(PY) manage.py makemigrations

.PHONY: migrate
migrate:  ## Apply DB migrations (build the schema)
	$(PY) manage.py migrate

.PHONY: seed
seed:  ## Load deck/card content from content/*.yaml into the DB
	$(PY) manage.py load_decks

.PHONY: setup
setup: install migrate seed  ## One-shot: install deps, build DB, load content
	@echo "\n✅ Ready. Run 'make run' and open http://127.0.0.1:$(PORT)\n"

.PHONY: run
run:  ## Start the dev server (migrates + seeds first)
	$(PY) manage.py migrate
	$(PY) manage.py load_decks
	$(PY) manage.py runserver $(PORT)

.PHONY: test
test:  ## Run the test suite
	$(PY) manage.py test

.PHONY: superuser
superuser:  ## Create an admin login (optional, for /admin)
	$(PY) manage.py createsuperuser

.PHONY: clean
clean:  ## Delete the local SQLite DB and cached audio
	rm -f db.sqlite3
	rm -rf media/audio_cache
