import requests
import configparser
from influxdb import InfluxDBClient
import logging
from logging.handlers import RotatingFileHandler
import os

# Set up configparser to read config.ini in this directory
config = configparser.RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
config.read('config.ini')

# SmartThings expects an "Authentication" header with the value
# "Bearer: <api key>"
KEY = 'Bearer ' + config.get('smartthings', 'smartthings_api_key')

# Influx database, user, and password
INFLUX_USER = config.get('influx', 'user')
INFLUX_PASSWORD = config.get('influx', 'password')
INFLUX_DATABASE = config.get('influx', 'database')

# Set up rotating file logging
LOG_NAME = config.get('logging', 'filename')
LOG_MAXBYTES = int(config.get('logging', 'maxBytes'))
LOG_BACKUPCOUNT = int(config.get('logging', 'backupCount'))
LOG_FORMAT = '%(asctime)-15s %(message)s'

logger = logging.getLogger('Logger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMAT)
handler = RotatingFileHandler(
    LOG_NAME, maxBytes=LOG_MAXBYTES, backupCount=LOG_BACKUPCOUNT)
handler.setFormatter(formatter)
logger.addHandler(handler)


class Device(object):
    def __init__(self):
        self.name = ''
        self.label = ''
        self.id = ''
        self.device_type_name = ''


class buttonDevice(Device):
    this_device_type_name = 'SmartSense Button'
    status_tags = []


class waterLeakDevice(Device):
    status_tags = ['temperatureMeasurement', 'battery', 'waterSensor']
    commands = ['configuration', 'refresh', 'healthCheck']
    this_device_type_name = 'SmartSense Moisture Sensor'

    def __init__(self):
        self.water = False
        self.temperature = 0.0
        self.battery = 0
        super().__init__()

    def send_data(self):
        water_leak_data = [
            {
                "measurement": "water_leak",
                "tags": {
                    "label": f"{self.label}"
                },
                "fields": {
                    "waterLeak": self.water,
                    "temperature": self.temperature,
                    "battery": self.battery,
                }
            }
        ]
        client = InfluxDBClient('localhost', 8086, username=INFLUX_USER,
                                password=INFLUX_PASSWORD, database=INFLUX_DATABASE)
        client.write_points(water_leak_data)
        logger.info(f'Wrote water leak data to influx: {self.label}')


class multiDevice(Device):
    this_device_type_name = 'SmartSense Multi Sensor'
    status_tags = []


class powerOutlet(Device):
    this_device_type_name = 'SmartPower Outlet'
    status_tags = []


class temperatureMeasurement(object):
    def __init__(self, timestamp, temperature, unit):
        self.timestamp = timestamp
        self.temperature = temperature
        self.unit = unit


logger.info('Start running script')
# get a list of all devices
r = requests.get('https://api.smartthings.com/v1/devices',
                 headers={'Authorization': KEY})

devices = r.json()['items']
device_list = []
influx_counted = 0

for device in devices:
    new_device = Device()
    new_device.name = device['name']
    new_device.label = device['label']
    new_device.id = device['deviceId']
    # A hub will appear as a device, but it will not have a
    # 'deviceTypeName' field so we can ignore it
    if 'deviceTypeName' in device:
        new_device.device_type_name = device['deviceTypeName']
    else:
        new_device.device_type_name = ''

    # Get device status
    status = requests.get(
        f'https://api.smartthings.com/v1/devices/{new_device.id}/status', headers={'Authorization': KEY})
    status_json = status.json()

    if new_device.device_type_name == waterLeakDevice.this_device_type_name:
        water_leak_sensor = waterLeakDevice()
        water_leak_sensor.label = new_device.label
        try:
            water_leak_sensor.battery = status_json['components']['main']['battery']['battery']['value']
            water_leak_sensor.temperature = status_json['components'][
                'main']['temperatureMeasurement']['temperature']['value']
            water_string = status_json['components']['main']['waterSensor']['water']['value']
            if water_string == 'dry':
                water_leak_sensor.water = False
            else:
                water_leak_sensor.water = True
            water_leak_sensor.send_data()
            influx_counted += 1
        except:
            print('failed water sensor')
    elif new_device.device_type_name == buttonDevice.this_device_type_name:
        button_device = buttonDevice()
        button_device.label = new_device.label
        try:
            button_device.battery = status_json['components']['main']['battery']['battery']['value']
            button_device.temperature = status_json['components'][
                'main']['temperatureMeasurement']['temperature']['value']

        except:
            print('failed button sensor')
    elif new_device.device_type_name == multiDevice.this_device_type_name:
        pass
    elif new_device.device_type_name == powerOutlet.this_device_type_name:
        pass

    device_list.append(new_device)

logger.info(
    f'Completed run with {influx_counted}/{len(devices) - 1} sensors uplaoded successfully')
