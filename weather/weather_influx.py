import requests
import logging
import os
from influxdb import InfluxDBClient
import schedule
import time

LOG_FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# openweather API key
API_KEY = os.environ["OPENWEATHER_API_KEY"]

# Influx configuration
INFLUX_DATABASE = os.environ["INFLUX_DATABASE"]
INFLUX_NAME = os.environ["INFLUX_NAME"]

# base_url variable to store url
base_url = "http://api.openweathermap.org/data/2.5/weather?"

# Get city name
city_id = os.environ["OPENWEATHER_CITY_ID"]

# complete_url variable to store
# complete url address
complete_url = base_url + "appid=" + API_KEY + "&id=" + city_id


def run_script():
    # get method of requests module
    # return response object
    response = requests.get(complete_url)

    logging.info(f"OpenWeather response: {response}")

    # json method of response object
    # convert json format data into
    # python format data
    x = response.json()

    # Now x contains list of nested dictionaries
    # Check the value of "cod" key is equal to
    # "404", means city is found otherwise,
    # city is not found
    if x["cod"] != "404":

        # store the value of "main"
        # key in variable y
        y = x["main"]

        # store the value corresponding
        # to the "temp" key of y
        current_temperature = y["temp"]

        # store the value corresponding
        # to the "pressure" key of y
        current_pressure = y["pressure"]

        # store the value corresponding
        # to the "humidity" key of y
        current_humidity = y["humidity"]

        clouds = x["clouds"]["all"]

        city_name = x["name"]

        # store the value of "weather"
        # key in variable z
        z = x["weather"]

        # store the value corresponding
        # to the "description" key at
        # the 0th index of z
        weather_description = z[0]["description"]

        # print following values
        logging.info(
            " Temperature (in kelvin unit) = "
            + str(current_temperature)
            + "\n atmospheric pressure (in hPa unit) = "
            + str(current_pressure)
            + "\n humidity (in percentage) = "
            + str(current_humidity)
            + "\n description = "
            + str(weather_description)
        )

        weather_data = [
            {
                "measurement": "weather",
                "tags": {"id": city_id, "name": city_name},
                "fields": {
                    "temperature": current_temperature,
                    "humidity": current_humidity,
                    "pressure": current_pressure,
                    "description": weather_description,
                    "clouds": clouds,
                },
            }
        ]
        client = InfluxDBClient(INFLUX_NAME, 8086, database=INFLUX_DATABASE)
        success = client.write_points(weather_data)
        logging.info(f"Influx write: {success}")
    else:
        logging.error(" City Not Found ")


run_script()

schedule.every(30).minutes.do(run_script)

while True:
    schedule.run_pending()
    time.sleep(1)
