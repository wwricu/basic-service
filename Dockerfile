FROM python:3.13-slim

ARG VERSION
ENV PYTHONOPTIMIZE=1 ENV=prod CONFIG_FILE=/etc/basic-service/config.json VERSION=${VERSION}
WORKDIR /data

ADD https://github.com/wwricu/basic-service/releases/latest/download/wwricu-0.0.0-py3-none-any.whl .

RUN pip3 install --disable-pip-version-check --no-cache-dir wwricu-0.0.0-py3-none-any.whl && rm -rf wwricu-0.0.0-py3-none-any.whl \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' > /etc/timezone

CMD ["uvicorn", "wwricu.main:app", "--host", "0.0.0.0", "--no-access-log", "--root-path", "/api"]
