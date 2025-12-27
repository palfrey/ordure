settings.yaml.base64: settings.yaml
	base64 settings.yaml > settings.yaml.base64

requirements.txt: requirements.in .tool-versions
	uv pip compile requirements.in -o requirements.txt --python-version 3.14 --no-strip-extras

.venv/bin/python:
	uv venv --python 3.14

sync: .venv/bin/python requirements.txt
	uv pip sync --strict requirements.txt

local-run: sync
	docker-compose up -d selenium
	REMOTE_SELENIUM=http://localhost:4444/wd/hub .venv/bin/python ordure.py

pyright: sync
	.venv/bin/pyright --pythonpath .venv/bin/python .

pre-commit: sync
	.venv/bin/pre-commit run -a
