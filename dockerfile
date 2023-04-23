FROM python:3.10

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

COPY ./app /src/app

RUN crontab crontab

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", ";" "crond", "-f"]
