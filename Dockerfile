FROM python:3.12-slim

COPY ./ /build


RUN pip3 install --user --disable-pip-version-check --no-cache-dir /build && rm -rf /build \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' > /etc/timezone

CMD ["wwricu"]
