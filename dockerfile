FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

COPY ./app /src/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]