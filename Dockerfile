FROM python:3.14-slim

ARG VERSION
ENV PYTHONOPTIMIZE=1 ENV=prod CONFIG_FILE=config.json VERSION=${VERSION}
WORKDIR /data

ADD https://github.com/wwricu/basic-service/releases/latest/download/wwricu-0.0.0-py3-none-any.whl .

RUN pip3 install --disable-pip-version-check --no-cache-dir wwricu-0.0.0-py3-none-any.whl && rm -rf wwricu-0.0.0-py3-none-any.whl

CMD ["uvicorn", "wwricu.main:app", "--host", "0.0.0.0", "--no-access-log"]
