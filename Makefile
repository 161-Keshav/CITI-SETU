.DEFAULT_GOAL := help
PYTHON ?= python
API_PORT ?= 8000

.PHONY: help setup data train-isolated train-fed train-central export eval docs test lint load-test demo clean api

help:
	@$(PYTHON) -c "print('Targets: setup data train-isolated train-fed train-central export eval docs test lint load-test demo clean')"

setup:
	$(PYTHON) -m pip install -e ".[dev]"

data:
	$(PYTHON) scripts/generate_data.py --seed 42

train-isolated train-fed train-central export:
	@$(PYTHON) -c "print('The lightweight demo uses the deterministic risk policy. Run make eval to reproduce its measured synthetic metrics.')"

eval:
	$(PYTHON) scripts/run_eval.py

docs:
	$(PYTHON) scripts/render_docs.py

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests scripts

load-test:
	$(PYTHON) scripts/run_eval.py --latency-only

api:
	$(PYTHON) -m uvicorn setu.serving.app:app --app-dir src --host 0.0.0.0 --port $(API_PORT)

demo: data eval
	@$(MAKE) api

clean:
	@$(PYTHON) -c "from pathlib import Path; [p.unlink() for p in [Path('audit.jsonl'), Path('results/metrics.json')] if p.exists()]"
