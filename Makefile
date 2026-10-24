settings.yaml.base64: settings.yaml Makefile
	base64 -w 0 settings.yaml > settings.yaml.base64

.venv/bin/python:
	uv venv --python 3.14

sync: .venv/bin/python
	uv sync

local-run: sync
	docker-compose up -d selenium
	REMOTE_SELENIUM=http://localhost:4444/wd/hub .venv/bin/python ordure.py

pyright: sync
	.venv/bin/pyright --pythonpath .venv/bin/python .

pre-commit: sync
	.venv/bin/pre-commit run -a
