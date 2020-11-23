FROM python:3
LABEL "Name"="weather_influx"
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD python weather_influx.py