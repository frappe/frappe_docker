# Help generator (targets with ##)
help: ## Show this help message
	@echo ""
	@echo "$(GREEN)Available make commands:$(RESET)"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# 1. Run all linters and formatters from pre-commit config
lint: ## Run all configured pre-commit hooks (includes formatting & checks)
	pre-commit run --all-files

# 2. Only run formatting hooks (e.g. Prettier, Black, Isort)
format: ## Run formatting-only hooks from pre-commit
	pre-commit run prettier --all-files || true
	pre-commit run black --all-files || true
	pre-commit run isort --all-files || true
	pre-commit run shfmt --all-files || true

# 3. Stage, commit & push
push: ## Add all files, commit (ask for message), and push
	@git add .
	@read -p "Enter commit message: " msg; \
	git commit -m "$$msg"
	@git push

# 4. Amend last commit (no edit)
amend: ## Amend last commit without editing the message
	git commit --amend --no-edit

# Add-ons:

check-hooks: ## Run all pre-commit hooks (full check)
	pre-commit run --all-files

install-hooks: ## Install pre-commit hooks in .git/hooks
	pre-commit install

reset-soft: ## Undo last commit but keep changes staged
	git reset --soft HEAD~1

clean: ## Remove temporary Python/node/docker files
	rm -rf __pycache__ node_modules *.pyc *.log .pytest_cache .mypy_cache
