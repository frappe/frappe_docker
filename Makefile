# Default help formatter
.DEFAULT_GOAL := help

# Colors
GREEN := \033[0;32m
RESET := \033[0m

# Help generator (targets with ##)
help: ## Show this help message
	@echo ""
	@echo "$(GREEN)Available make commands:$(RESET)"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# 1. Pre-commit check: trailing whitespace only
lint: ## Run pre-commit check for trailing whitespace
	pre-commit run trailing-whitespace --all-files

# 2. Format all files with prettier
format: ## Run Prettier on the whole repo
	npx prettier --write .

# 3a-c. Stage, commit & push
push: ## Add all files, commit (ask for message), and push
	@git add .
	@read -p "Enter commit message: " msg; \
	git commit -m "$$msg"
	@git push

# 4. Amend last commit (no edit)
amend: ## Amend last commit without editing the message
	git commit --amend --no-edit

# Add-ons you might like:

check-hooks: ## Run all configured pre-commit hooks
	pre-commit run --all-files

install-hooks: ## Install pre-commit hooks in .git/hooks
	pre-commit install

reset-soft: ## Undo last commit but keep changes staged
	git reset --soft HEAD~1

clean: ## Remove temporary Python/node/docker files
	rm -rf __pycache__ node_modules *.pyc *.log .pytest_cache .mypy_cache
