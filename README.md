# wwr.icu service

## Dev

```
$ pip install uv
$ uv sync
```

`$ fastapi dev .\wwricu\main.py` or `$ uvicorn wwricu.main:app --reload`

## Environment variables

| Variable name        | Description                  | Default         | Default in Docker |
|----------------------|------------------------------|-----------------|-------------------|
| CF_ACCOUNT_ID        | Cloudflare account id        | N/A             | N/A               |
| CF_API_TOKEN         | Cloudflare api token         | N/A             | N/A               |
| ENV                  | Specify running environgment | dev             | prod              |
| LOG_PATH             | Path                         | logs            | logs              |
| CONFIG_FILE          | Config file kv store key     | dev.config.json | config.json       |
