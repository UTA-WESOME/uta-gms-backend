# UTA GMS BACKEND

## How to run
```commandline
cd utagms
docker-compose up --build
```
#### How to run bash in docker
```commandline
docker exec -it uta_gms_django bash
```
##### How to run Tests
run all tests at once from docker bash:
```commandline
python manage.py test
```

## Database Schema
<img src="/dbSchema.png" />
