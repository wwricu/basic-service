FROM python:3.10

COPY ./ /fastapi
WORKDIR /fastapi

RUN pip3 install --upgrade pip \
&& pip3 install --no-cache-dir --upgrade -r /fastapi/requirements.txt \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo 'Asia/Shanghai' >/etc/timezone

CMD ["uvicorn",
     "main:app",
     "--app-dir", "./src",
     "--proxy-headers",
     "--host", "0.0.0.0",
     "--port", "8000",
     "--root-path", "/api"]
