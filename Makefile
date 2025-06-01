PRECOMMIT=pre-commit

.PHONY: help
help: ## Show this help
	 @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
			awk 'BEGIN {FS = ":.*?## "; printf "Usage:\n\tmake \033[36m<target>\033[0m\nTargets:\n"}; {printf "\t\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## Init pre-commit hooks
	$(info * Installing pre-commit hooks)
	@# Run this command to autoupdate pre-commit hooks:
	@# $ pre-commit autoupdate
	$(PRECOMMIT) install --install-hooks

.PHONY: requirements
requirements: ## Install locally all requirements
	$(info * Running asdf install)
	asdf install

.PHONY: validate
validate: ## Run Pre-commit against all files
	$(info * Pre-commit run)
	$(PRECOMMIT) run --all-files

.PHONY: up
up: ## docker-compose up
	docker-compose up -d

.PHONY: stop
stop: ## docker-compose stop
	docker-compose down

.PHONY: ps
ps: ## docker-compose ps
	docker-compose ps

.PHONY: logs
logs: ## Show docker-compose logs
	docker-compose logs -f
