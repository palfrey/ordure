settings.yaml.base64: settings.yaml
	base64 settings.yaml > settings.yaml.base64

requirements.txt: requirements.in .tool-versions
	uv pip compile requirements.in -o requirements.txt --python-version 3.9 --no-strip-extras

.venv/bin/python:
	uv venv --python 3.9

sync: .venv/bin/python requirements.txt
	uv pip sync --strict requirements.txt
