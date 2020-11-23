FROM python:3
LABEL "Name"="smartthings_influx"
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD python smartthings_influx.py