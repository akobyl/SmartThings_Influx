# SmartThings InfluxDB Generator

This script will run once and write influx data to a local instance.  This data can then be recorded and plotted over time with a tool such as Grafana:

![Temperatureplot](doc/temperature_plot.png)

## Python setup

1. Create a virtual environment: `python -m venv /path/to/env`
2. Activate the virtual environment `source /path/to/env/bin/activate`
3. Install all dependencies `pip install -r requirements.txt`

## SmartThings API Key

The first step is to create a SmartThings API key which has access
to device statuses and devise lists

1. Create/Log in to your [Samsung Developer's Account](https://graph.api.smartthings.com/)
2. Create a new token at [Samsung Personal Access Tokens](https://account.smartthings.com/tokens)
3. Create a token with permissions to  (devices) list all devices, see all devices, (profiles) see all device profiles, and see locations

## InfluxDB Setup

Create a new user and database in InfluxDB for this script: [Influx Authentication and Authorization](https://docs.influxdata.com/influxdb/v1.8/administration/authentication_and_authorization/)

The new Influx user should have permissions to read and write to only the new smartthings database.

## Set up Cron for automation

If you want this script to run periodically, the quickest way is to set up the script as a new cron job.  Be sure to use the virtual environment python executable (if using virtual environments)

For example, to run this script every 5 minutes add this line to `crontab -e`:

`*/5 * * * * /home/myuser/smartthings/smartthings-env/bin/python /home/myuser/smartthings/smartthings_influx.py`
