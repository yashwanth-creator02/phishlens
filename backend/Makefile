PY ?= python
.PHONY: install dev test train-demo run lint
install:
	$(PY) -m pip install -r requirements-dev.txt
train-demo:      ## trains on SYNTHETIC data: pipeline check only
	$(PY) -m training.train --source synthetic --n 2400 --out models --reports reports --activate
test:
	$(PY) -m pytest -q
run:
	$(PY) -m uvicorn app.main:app --reload --port 8000
