import time
import datetime
import sqlite3
from threading import Thread

import numpy as np
from bokeh.embed import server_document
from bokeh.server.server import Server
import bokeh.io
import bokeh.models
import bokeh.plotting
import bokeh.driving

import board
import busio

import adafruit_veml7700
import adafruit_veml6070
import adafruit_sgp30
import adafruit_bme280

from flask import Flask, jsonify, render_template
from tornado.ioloop import IOLoop

app = Flask(__name__)

# Database names
db = "environmental_monitor.db"
# Sample frequency in seconds
sample_frequency = 2

# Create busio I2C
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# Create objects
light = adafruit_veml7700.VEML7700(i2c)
light.light_gain = light.ALS_GAIN_1_8
light.light_integration_time = light.ALS_25MS

uv = adafruit_veml6070.VEML6070(i2c)

bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
sgp30.iaq_init()
sgp30.set_iaq_baseline(0x8973, 0x8aae)

def read_sensors():
    """Read sensors every `sample_frequency` seconds and write to `db` database."""
    previous_time = datetime.datetime.now()
    while True:
        now = datetime.datetime.now()
        delta = now - previous_time
        if delta.seconds >= sample_frequency:
            previous_time = now
            
            # Read SGP30.
            eCO2_data = sgp30.eCO2
            tvoc_data = sgp30.TVOC

            # Read VEML6070 and VEML7700, sample ten times.
            for j in range(10):
                light_data = light.lux
                uv_raw = uv.uv_raw
                uv_data = uv.get_index(uv_raw)

            # Read BME280.
            temp_data = bme280.temperature
            # Convert temperature (C->F)
            temp_data = int(temp_data) * 1.8 + 32
            humid_data = bme280.humidity
            pressure_data = bme280.pressure

            # Write to database
            conn = sqlite3.connect(db)
            curs = conn.cursor()
            curs.execute("INSERT INTO data values(?, ?, ?, ?, ?, ?, ?, ?)",
            (now, temp_data, humid_data, pressure_data, eCO2_data, tvoc_data,
            light_data, uv_data))
            conn.commit()
            conn.close()
            
@app.route('/_get_last_data')
def get_last_data():
    conn = sqlite3.connect(db)
    curs = conn.cursor()
    for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
        now_string = row[0]#.strftime("%Y-%m-%d %H:%M:%S")
        temp_data = row[1]
        humid_data = row[2]
        pressure_data = row[3]
        eCO2_data = row[4]
        tvoc_data = row[5]
        light_data = row[6]
        uv_data = row[7]
    conn.close()
    return jsonify(temp_data=temp_data, humid_data=humid_data, pressure_data=pressure_data, eCO2_data=eCO2_data,
    tvoc_data=tvoc_data, light_data=light_data, uv_data=uv_data, now=now_string)

@app.route('/')
def index():
    return render_template('index.html')

Thread(target=read_sensors).start()

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
