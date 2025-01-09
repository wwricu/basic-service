FROM python:3.12-slim

RUN pip3 install --user --disable-pip-version-check --no-cache-dir wwricu \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' > /etc/timezone

CMD ["wwricu"]
