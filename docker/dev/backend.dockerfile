FROM python:3.10

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install psycopg dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    glpk-utils \
    && rm -rf /var/lib/apt/lists/*

COPY ./utagms/requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
