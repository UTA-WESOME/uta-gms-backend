# uta-gms-backend

The uta-gms-backend is an application designed to manage user data, use the [uta-gms-engine](https://github.com/UTA-WESOME/uta-gms-engine) package to obtain results for the UTA-GMS method, and provide data to the [uta-gms-frontend](https://github.com/UTA-WESOME/uta-gms-frontend). It is written entirely in Python 3.10 using the Django framework 4.2.3. PostgreSQL 15 has been
chosen as the database management system. The entire application is containerized using Docker.
The application allows connecting through a REST API, enabling users to retrieve, create,
update, and delete data. Additionally, users can run the UTA-GMS algorithm for their data using
the uta-gms-engine library inside the uta-gms-backend app. Authentication and authorization
are handled using JSON Web Tokens.

## How to run? 🚀

There are 3 options to run the application. The first one uses image available on DockerHub while the two former ones can be used if you prefer to clone the repo and build it locally.

### Use image from DockerHub

```commandline
docker run --name uta-gms-backend -e SECRET_KEY= -e ALLOWED_HOSTS= -e DATABASE_URL= anras5/uta-gms-backend
```
- `SECRET_KEY` - prefferably a long random set of characters
- `ALLOWED_HOSTS` - list of hosts to allow connections from, e.g. `*`
- `DATABASE_URL` - database connection string, e.g. `postgres://postgres:postgres@uta-gms-postgres:5432/postgres`

---

### Develop

1. Prepare a `.env` file inside the `utagms` directory. Example:
```
DEBUG=True
SECRET_KEY='some_secret'
ALLOWED_HOSTS=*
DATABASE_URL=postgres://postgres:postgres@uta-gms-postgres:5432/postgres

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
```

2. Run with Docker:

```commandline
cd docker/dev
docker compose up --build
```

---

### Develop with custom `uta-gms-engine` version

Copy your `uta-gms-engine` build file into the `engine` directory. Remember that the version has to be higher than the
current one on PyPI.

```commandline
cp /path/to/uta_gms_engine-version-py3-none-any.whl engine/
cd docker/dev-custom-engine
docker compose up --build
```

## Technologies used 🔨
- [Python](https://www.python.org/)
- [django-REST-framework](https://www.django-rest-framework.org/)
- [PostgreSQL 15](https://www.postgresql.org/about/news/postgresql-15-released-2526/)
- [Docker](https://www.docker.com/)
- [JWT](https://jwt.io/)
- [uta-gms-engine](https://github.com/UTA-WESOME/uta-gms-engine)

## Database Schema 🗺️

![database schema](./uta-gms-backend-ER-diagram.png)
