import time
import datetime

import board
import busio

import adafruit_veml7700
import adafruit_veml6070
import adafruit_sgp30
import adafruit_bme280

from flask import Flask, jsonify, render_template

app = Flask(__name__)

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

@app.route('/_read_sensors')
def read_sensors():
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
    # convert temperature (C->F)
    temp_data = int(temp_data) * 1.8 + 32
    humid_data = bme280.humidity
    pressure_data = bme280.pressure

    now = datetime.datetime.now()
    now_string = now.strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify(temp_data=temp_data, humid_data=humid_data, pressure_data=pressure_data, eCO2_data=eCO2_data,
    tvoc_data=tvoc_data, light_data=light_data, uv_data=uv_data, now=now_string)

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
