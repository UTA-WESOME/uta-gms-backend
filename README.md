# uta-gms-backend

The uta-gms-backend is an application designed to manage user data, use the [uta-gms-engine](https://github.com/UTA-WESOME/uta-gms-engine) package to obtain results for the UTA-GMS method, and provide data to the [uta-gms-frontend](https://github.com/UTA-WESOME/uta-gms-frontend). It is written entirely in Python 3.10 using the Django framework 4.2.3 and Celery 5.4.6. The app needs PostgreSQL 15 and Redis 7 configured to work properly. The default environment for running the application is Docker containers. The application allows connecting through a REST API, enabling users to manage their projects. Additionally, users can run the UTA-GMS method for their data using the uta-gms-engine library inside the uta-gms-backend app via Celery. Authentication and authorization are handled using JSON Web Tokens.

## How to run? 🚀

The preferred way to run the app is by using Docker Compose. You can configure and run it in other ways (e.g. locally), however it is not advised for development. You can also pull Docker images from DockerHub.

### Docker compose

1. Prepare a `.env` file inside the `utagms` directory. Example:
```
DEBUG=True
SECRET_KEY='some_secret'
ALLOWED_HOSTS=*
DATABASE_URL=postgres://postgres:postgres@uta-gms-postgres:5432/postgres

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

CELERY_BROKER=redis://uta-gms-redis:6379/0
CELERY_CACHE=django-cache
CELERY_BACKEND=django-db
```
2. Run with Docker Compose:

```commandline
cd docker/dev
docker compose up --build
```

### Images on DockerHub

1. [Django](https://hub.docker.com/r/anras5/uta-gms-django)
2. [Celery](https://hub.docker.com/r/anras5/uta-gms-celery)

## Technologies used 🔨
- [Python](https://www.python.org/)
- [django-REST-framework](https://www.django-rest-framework.org/)
- [PostgreSQL 15](https://www.postgresql.org/about/news/postgresql-15-released-2526/)
- [Docker](https://www.docker.com/)
- [JWT](https://jwt.io/)
- [Celery](https://docs.celeryq.dev/en/stable/index.html)
- [uta-gms-engine](https://github.com/UTA-WESOME/uta-gms-engine)

## Database Schema 🗺️

![database schema](./uta-gms-backend-ER-diagram.png)
