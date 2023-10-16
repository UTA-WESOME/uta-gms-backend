# UTA GMS BACKEND

## How to run

### develop

```commandline
cd docker/dev
docker compose up --build
```

---

### develop with custom `uta-gms-engine` version

Copy your `uta-gms-engine` build file into the `engine` directory. Remember that the version has to be higher than the
current one on PyPI.

```commandline
cp /path/to/uta_gms_engine-version-py3-none-any.whl engine/
cd docker/dev-custom-engine
docker compose up --build
```

## Database Schema

![database schema](./uta-gms-backend-ER-diagram.png)
