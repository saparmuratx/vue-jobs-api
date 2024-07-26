FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --upgrade -r /code/requirements.txt

COPY ./src /code/src
COPY ./jobs.db /code/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80" , "--workers", "4"]
