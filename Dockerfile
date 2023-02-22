FROM python:slim

COPY ./ /fastapi
WORKDIR /fastapi

ENV PIP_ROOT_USER_ACTION=ignore
RUN pip3 install --disable-pip-version-check \
--no-cache-dir -r /fastapi/requirements.txt \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo 'Asia/Shanghai' > /etc/timezone

CMD ["uvicorn", "main:app", \
     "--app-dir", "./src", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*",\
     "--root-path", "/api"]
