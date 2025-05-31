FROM python:3.11

WORKDIR /usr/src/app

USER root

RUN python -m pip install --upgrade pip
COPY . .
COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
