FROM python:3.10.9-slim

COPY ./ /fastapi
WORKDIR /fastapi

ENV PIP_ROOT_USER_ACTION=ignore
RUN pip3 install --disable-pip-version-check \
--no-cache-dir -r /fastapi/requirements.txt \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo 'Asia/Shanghai' > /etc/timezone

CMD ["uvicorn", "main:app", \
     "--app-dir", "./src", \
     "--proxy-headers", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--root-path", "/api"]
