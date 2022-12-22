FROM python:3.10

COPY ./src /code/app
COPY ./requirements.txt /code/requirements.txt
WORKDIR /code/app

RUN pip3 install --upgrade pip \
&& pip3 install --no-cache-dir --upgrade -r /code/requirements.txt \
&& ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo 'Asia/Shanghai' >/etc/timezone

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
