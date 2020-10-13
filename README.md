# Raspberry Pi Environmental Monitor
*Inspired by [Adafruit IO Environmental Monitor for Feather or Raspberry Pi by Brent Rubell](https://learn.adafruit.com/adafruit-io-air-quality-monitor).*

## Description
Monitor temperature, humidity, pressure, equivalent CO2, total volatile organic compounds, light level, and UV level using [BME280](https://www.adafruit.com/product/2652), [SGP30](https://www.adafruit.com/product/3709), [VEML7700](https://www.adafruit.com/product/4162), and [VEML6070](https://www.adafruit.com/product/2899) sensors from Adafruit. Sensors are connected to a Raspberry Pi Zero W using the I2C protocol.

<img src="/images/hardware.jpg" alt="Photograph of Raspberry Pi Environmental Monitor" width="300">

The Raspberry Pi runs a Flask application that reads the data from the sensors, writes to a SQLite database, and displays the most recent data as well as live-updating plots on a web page.

<img src="/images/web_interface.png" alt="Screenshot of web interface" width="300">

## Software dependencies
### Libraries for interfacing with sensors
- [Adafruit Blinka](https://pypi.org/project/Adafruit-Blinka/)
- Adafruit CircuitPython drivers
  - [BME280](https://github.com/adafruit/Adafruit_CircuitPython_BME280)
  - [SGP30](https://github.com/adafruit/Adafruit_CircuitPython_SGP30)
  - [VEML7700](https://github.com/adafruit/Adafruit_CircuitPython_VEML7700)
  - [VEML6070](https://github.com/adafruit/Adafruit_CircuitPython_VEML6070)
### Web tools
- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [jQuery](https://github.com/jquery/jquery)
### Data processing and visualization
- [NumPy](https://numpy.org/)
- [SQLite](https://www.sqlite.org/index.html)
- [Bokeh](https://docs.bokeh.org/en/latest/index.html)
