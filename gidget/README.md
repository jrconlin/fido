# Install

This presumes you're using CircuitPython 8.

You'll need to copy into `/lib`:

* `adafruit_minimqtt/*`
* `adafruit_register/*`
* `adafruit_binascii.mpy`
* `adafruit_st7789.mpy`
* `circuitpython_base64.mpy`
* `simpleio.mpy`


`settings.toml` should contain:

* `WIFI_SSID` = Wifi Network SSID
* `WIFI_PASSWORD` = Wifi Network Password
* `MQTT_HOST` = Hostname for MQTT server
* `MQTT_USER` = Username
* `MQTT_PASS` = Password
* `MQTT_PUB`  = Publication path (if different than the default `fido/image`)

# This does not work on a Pico W

Yeah, turns out that python isn't the most efficient thing in the world to run on a small platform.
Once this app loads and gets rolling, it really doesn't leave much RAM left. 

I could possibly hand code to remove a lot of the extra stuff that will never be used in MQTT and the display routines, but meh. 
