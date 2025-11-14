FROM python:3.11

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . /app

CMD uvicorn --host=0.0.0.0 app.main:app


