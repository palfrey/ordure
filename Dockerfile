FROM python:3.14
WORKDIR /app
RUN curl -o /usr/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/81b1373f17855a4dc21156cfe1694c31d7d1792e/wait-for-it.sh && chmod +x /usr/bin/wait-for-it
RUN curl -LsSf https://astral.sh/uv/0.13.5/install.sh | sh
COPY pyproject.toml uv.lock /app/
RUN ~/.local/bin/uv sync
COPY . .
CMD .venv/bin/python -u ordure.py
