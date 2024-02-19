FROM python:3.10

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install psycopg dependencies, GLPK and Java
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    glpk-utils \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# get sampler java package and setup env variables
RUN mkdir /sampler && \
    wget -O /sampler/polyrun-1.1.0-jar-with-dependencies.jar https://github.com/kciomek/polyrun/releases/download/v1.1.0/polyrun-1.1.0-jar-with-dependencies.jar
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64
ENV PATH $PATH:$JAVA_HOME/bin

ADD ./utagms .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

CMD ["sh", "-c", "python manage.py migrate && gunicorn utagms.wsgi --timeout 120"]
