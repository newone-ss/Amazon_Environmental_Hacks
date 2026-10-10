# Bhujal Makefile
# ──────────────────────────────────────────────

.PHONY: data package score test dev deploy lint format clean

# ── Data pipeline ──────────────────────────────
data:
	python -m pipeline.build_derived

# ── Package (SAM Lambda bundle) ────────────────
package:
	python -m pipeline.package

# ── Scoring ────────────────────────────────────
score:
	python -m scoring.run

# ── Tests ──────────────────────────────────────
test:
	pytest tests/ -v --tb=short

# ── Lint & format ──────────────────────────────
lint:
	ruff check . --fix
	mypy scoring/ backend/ --ignore-missing-imports

format:
	ruff format .

# ── Dev servers ────────────────────────────────
dev:
	@echo "Starting backend on :8000 ..."
	cd backend && uvicorn app:app --reload --port 8000 &
	@echo "Starting frontend on :5173 ..."
	cd frontend && npm run dev

# ── Deploy (SAM) ───────────────────────────────
deploy:
	cd infra && sam build && sam deploy --guided

# ── Clean ──────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf infra/.aws-sam
