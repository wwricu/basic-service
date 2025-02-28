FROM python:3.12-slim

ENV PYTHONOPTIMIZE=1 ROOT_PATH=/api ENV=production
WORKDIR /data

ADD https://github.com/wwricu/basic-service/releases/latest/download/wwricu.tar.gz .
COPY version.txt .
COPY alembic.ini .

RUN pip3 install --disable-pip-version-check --no-cache-dir wwricu.tar.gz && rm -rf wwricu.tar.gz \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' > /etc/timezone

CMD ["wwricu"]
