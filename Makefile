.PHONY: dev build preview install scrape process embed build-db complete clean backup help

# Development
dev:
	bun run dev

build:
	bun run build

preview:
	bun run preview

install:
	bun install

# Data pipeline
scrape:
	uv run python scripts/scraper.py

process:
	uv run python scripts/process_icons.py

embed:
	uv run python scripts/embed_single_process.py

build-db:
	uv run python scripts/build_db.py

# Complete build pipeline
complete:
	uv run python scripts/build_complete_project.py

# Utilities
backup:
	mkdir -p backups && cp static/icons.db backups/icons_db_backup_$$(date +%Y%m%d_%H%M%S).db 2>/dev/null || true

clean:
	rm -rf dist node_modules .vite

help:
	@echo "Windows 98 Icons Search - Available commands:"
	@echo "  dev      - Start development server"
	@echo "  build    - Build for production"
	@echo "  preview  - Preview production build"
	@echo "  install  - Install dependencies"
	@echo "  scrape   - Scrape icons from web"
	@echo "  process  - Generate AI descriptions"
	@echo "  embed    - Create vector embeddings"
	@echo "  build-db - Build SQLite database"
	@echo "  complete - Run complete build pipeline"
	@echo "  backup   - Backup current database"
	@echo "  clean    - Remove build artifacts"