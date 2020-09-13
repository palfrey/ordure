FROM python:3.7
WORKDIR /app
RUN curl -o /usr/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/81b1373f17855a4dc21156cfe1694c31d7d1792e/wait-for-it.sh && chmod +x /usr/bin/wait-for-it
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
CMD python ordure.py