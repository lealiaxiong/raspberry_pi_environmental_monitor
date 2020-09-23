import time
import datetime
import sqlite3
from multiprocessing import Process

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
            

def get_last_data():
    conn = sqlite3.connect(db)
    curs = conn.cursor()
    for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
        now_string = row[0]
        temp_data = row[1]
        humid_data = row[2]
        pressure_data = row[3]
        eCO2_data = row[4]
        tvoc_data = row[5]
        light_data = row[6]
        uv_data = row[7]
    
    conn.close()
    
    return now_string, temp_data, humid_data, pressure_data, eCO2_data, tvoc_data, light_data, uv_data

@app.route('/_get_last_data')
def show_last_data():
    now_string, temp_data, humid_data, pressure_data, eCO2_data, tvoc_data, light_data, uv_data = get_last_data()
    return jsonify(temp_data=temp_data, humid_data=humid_data, pressure_data=pressure_data, eCO2_data=eCO2_data,
    tvoc_data=tvoc_data, light_data=light_data, uv_data=uv_data, now=now_string)
    
def get_num_datapoints(db):
    conn = sqlite3.connect(db)
    curs = conn.cursor()
    
    for row in curs.execute("SELECT COUNT(timestamp) FROM data"):
        num_datapoints = row[0]
    
    conn.close()
    
    return num_datapoints

def bkapp(doc):
    num_datapoints = get_num_datapoints(db)
    rollover = 300

    conn = sqlite3.connect("environmental_monitor.db")
    curs = conn.cursor()
    
    curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT " 
    + str(min(rollover, num_datapoints)))

    db_data = curs.fetchall()
    
    datatype_names = ("timestamps", "temps", "humidities", "pressures", "eCO2s", "tvocs", "lights", "uvs")
    data_lists = ([] for name in datatype_names)

    data = dict(zip(datatype_names, data_lists))
    
    for row in reversed(db_data):
        for datatype, datapoint in zip(data, row):
            data[datatype].append(datapoint)
            
    for i, timestamp in enumerate(data['timestamps']):
        data['timestamps'][i] = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        
    source = bokeh.models.ColumnDataSource(data=data)
    
    p_light = bokeh.plotting.figure(
        frame_width=500,
        frame_height=175,
        x_axis_label="time",
        y_axis_label="light (lux)",
        x_axis_type="datetime"
    )
    p_light.xaxis.formatter=bokeh.models.DatetimeTickFormatter(
        seconds = ['%H:%M:%S'],
        minutes = ['%H:%M:%S'],
        hourmin = ['%H:%M:%S'],
        days = ['%Y-%m-%d %H:%M:%S'],
        months = ['%Y-%m-%d %H:%M:%S'],
    )
    p_light.x_range.range_padding = 0
    
    light_line = p_light.line(source=source, x="timestamps", y="lights")
    
    @bokeh.driving.linear()
    def update(step):
        last_data = [[data] for data in get_last_data()]
        update_dict = dict(zip(datatype_names, last_data))
        timestamp = update_dict['timestamps'][0]
        update_dict['timestamps'][0] = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        source.stream(update_dict, rollover)
    
    doc.add_root(p_light)
        
    pc = doc.add_periodic_callback(update, sample_frequency*1000)
        

@app.route('/')
def index():
    script = server_document("http://192.168.0.106:5006/bkapp")
    return render_template('index.html', script=script, template="Flask")
    
def bk_worker():
    server = Server({'/bkapp': bkapp}, io_loop=IOLoop(), allow_websocket_origin=["localhost:5000", "0.0.0.0:5000", "192.168.0.106:5000", "192.168.0.106:5006"])
    server.start()
    server.io_loop.start()

process_read = Process(target=read_sensors)
process_plot = Process(target=bk_worker)

process_read.start()
process_plot.start()

if __name__ == '__main__':
	app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
