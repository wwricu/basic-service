# wwr.icu service

## Dev

```
$ pip install uv
$ uv sync
```

`$ fastapi dev .\wwricu\main.py` or `$ uvicorn wwricu.main:app --reload`


## Test

`$ pytest` to test all

or

`$ pytest test/api/test_open.py::test_open_get_about` to test single function

## Deploy

```
$ docker run \
    -v config.json:/etc/basic-service/config.json \
    -v <your workdir path>:/data \
    -e AWS_ACCESS_KEY_ID=<AWS access key id> \
    -e AWS_SECRET_ACCESS_KEY=<AWS access key secret> \
    -p 8000:8000 -d wwricu/basic-service:latest
```

or see [Deploy Actions Repo](https://github.com/wwricu/deploy/actions/workflows/dev_service.yml)

## Environment variables

| Variable name         | Description                     | Default     | Default in Docker              |
|-----------------------|---------------------------------|-------------|--------------------------------|
| AWS_ACCESS_KEY_ID     | Key id for aws service          | N/A         | N/A                            |
| AWS_SECRET_ACCESS_KEY | key secret for aws service      | N/A         | N/A                            |
| ENV                   | Specify running environgment    | local       | prod                           |
| LOG_PATH              | Path                            | logs        | logs                           |
| ROOT_PATH             | The root path app is running on | /           | /api                           |
| CONFIG_FILE           | Config file path                | config.json | /etc/basic-service/config.json |
