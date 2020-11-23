import schedule
import requests
from influxdb import InfluxDBClient
import logging
import os
import time

# SmartThings expects an "Authentication" header with the value
# "Bearer: <api key>"
SMARTTHINGS_API_KEY = os.environ["SMARTTHINGS_API_KEY"]
KEY = "Bearer " + SMARTTHINGS_API_KEY

# Influx configuration
INFLUX_NAME = os.environ["INFLUX_NAME"]
INFLUX_DATABASE = os.environ["INFLUX_DATABASE"]

LOG_FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class Device(object):
    def __init__(self):
        self.name = ""
        self.label = ""
        self.id = ""
        self.device_type_name = ""


class buttonDevice(Device):
    this_device_type_name = "SmartSense Button"
    status_tags = []

    def __init__(self):
        self.temperature = 0.0
        self.battery = 0
        super().__init__()

    def send_data(self):
        button_data = [
            {
                "measurement": "button",
                "tags": {"label": f"{self.label}"},
                "fields": {
                    "temperature": self.temperature,
                    "battery": self.battery,
                },
            }
        ]
        client = InfluxDBClient(INFLUX_NAME, 8086, database=INFLUX_DATABASE)
        client.write_points(button_data)
        logging.info(f"Wrote button data to influx: {self.label}")


class waterLeakDevice(Device):
    status_tags = ["temperatureMeasurement", "battery", "waterSensor"]
    commands = ["configuration", "refresh", "healthCheck"]
    this_device_type_name = "SmartSense Moisture Sensor"

    def __init__(self):
        self.water = False
        self.temperature = 0.0
        self.battery = 0
        super().__init__()

    def send_data(self):
        water_leak_data = [
            {
                "measurement": "water_leak",
                "tags": {"label": f"{self.label}"},
                "fields": {
                    "waterLeak": self.water,
                    "temperature": self.temperature,
                    "battery": self.battery,
                },
            }
        ]
        client = InfluxDBClient(INFLUX_NAME, 8086, database=INFLUX_DATABASE)
        client.write_points(water_leak_data)
        logging.info(f"Wrote water leak data to influx: {self.label}")


class multiDevice(Device):
    this_device_type_name = "SmartSense Multi Sensor"
    status_tags = [
        "battery",
        "temperature",
        "contactSensor",
        "accelerationSensor",
        "threeAxis",
    ]

    def __init__(self):
        self.battery = 0
        self.temperature = 0.0
        self.contactSensor = False
        self.threeAxis = []
        self.acceleration = False
        super().__init__()

    def send_data(self):
        multi_sensor_data = [
            {
                "measurement": "multi_sensor",
                "tags": {"label": f"{self.label}"},
                "fields": {
                    "temperature": self.temperature,
                    "battery": self.battery,
                },
            }
        ]
        client = InfluxDBClient(INFLUX_NAME, 8086, database=INFLUX_DATABASE)
        client.write_points(multi_sensor_data)
        logging.info(f"Wrote multisensor data to influx: {self.label}")


class powerOutlet(Device):
    this_device_type_name = "SmartPower Outlet"
    status_tags = []

    def __init__(self):
        self.power = 0.0
        super().__init__()

    def send_data(self):
        power_outlet_data = [
            {
                "measurement": "power_outlet",
                "tags": {"label": f"{self.label}"},
                "fields": {
                    "power": self.power,
                },
            }
        ]
        client = InfluxDBClient(INFLUX_NAME, 8086, database=INFLUX_DATABASE)
        client.write_points(power_outlet_data)
        logging.info(f"Wrote power data to influx: {self.label}")


class temperatureMeasurement(object):
    def __init__(self, timestamp, temperature, unit):
        self.timestamp = timestamp
        self.temperature = temperature
        self.unit = unit


def run_script():
    logging.info("Start running script")
    # get a list of all devices
    r = requests.get(
        "https://api.smartthings.com/v1/devices", headers={"Authorization": KEY}
    )

    devices = r.json()["items"]
    device_list = []
    influx_counted = 0

    for device in devices:
        new_device = Device()
        new_device.name = device["name"]
        new_device.label = device["label"]
        new_device.id = device["deviceId"]
        # A hub will appear as a device, but it will not have a
        # 'deviceTypeName' field so we can ignore it
        if "deviceTypeName" in device:
            new_device.device_type_name = device["deviceTypeName"]
        else:
            new_device.device_type_name = ""

        # Get device status
        status = requests.get(
            f"https://api.smartthings.com/v1/devices/{new_device.id}/status",
            headers={"Authorization": KEY},
        )
        status_json = status.json()

        if new_device.device_type_name == waterLeakDevice.this_device_type_name:
            water_leak_sensor = waterLeakDevice()
            water_leak_sensor.label = new_device.label
            try:
                water_leak_sensor.battery = status_json["components"]["main"][
                    "battery"
                ]["battery"]["value"]
                water_leak_sensor.temperature = status_json["components"]["main"][
                    "temperatureMeasurement"
                ]["temperature"]["value"]
                water_string = status_json["components"]["main"]["waterSensor"][
                    "water"
                ]["value"]
                if water_string == "dry":
                    water_leak_sensor.water = False
                else:
                    water_leak_sensor.water = True
                water_leak_sensor.send_data()
                influx_counted += 1
            except:
                logging.warning("failed water sensor")
        elif new_device.device_type_name == buttonDevice.this_device_type_name:
            button_device = buttonDevice()
            button_device.label = new_device.label
            try:
                button_device.battery = status_json["components"]["main"]["battery"][
                    "battery"
                ]["value"]
                button_device.temperature = status_json["components"]["main"][
                    "temperatureMeasurement"
                ]["temperature"]["value"]
                button_device.send_data()
                influx_counted += 1
            except:
                logging.warning("failed button sensor")
        elif new_device.device_type_name == multiDevice.this_device_type_name:
            multi_device = multiDevice()
            multi_device.label = new_device.label
            try:
                multi_device.battery = status_json["components"]["main"]["battery"][
                    "battery"
                ]["value"]
                multi_device.temperature = status_json["components"]["main"][
                    "temperatureMeasurement"
                ]["temperature"]["value"]
                multi_device.send_data()
                influx_counted += 1
            except:
                logging.warning("failed multi sensor")
        elif new_device.device_type_name == powerOutlet.this_device_type_name:
            outlet_device = powerOutlet()
            outlet_device.label = new_device.label
            try:
                outlet_device.power = status_json["components"]["main"]["powerMeter"][
                    "power"
                ]["value"]
                outlet_device.send_data()
                influx_counted += 1
            except:
                logging.warning("failed outlet sensor")

        device_list.append(new_device)

    logging.info(
        f"Completed run with {influx_counted}/{len(devices) - 1} sensors uploaded successfully"
    )


schedule.every(5).minutes.do(run_script)

while True:
    schedule.run_pending()
    time.sleep(1)
    