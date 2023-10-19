import paho.mqtt.client as mqtt
import json
import requests
import logging
import os
import time

from io import BytesIO
from PIL import Image
from ST7789 import ST7789

# My display is 1.2 inches
WIDTH = 320
HEIGHT = 240
# My camera makes a larger image than we need, so
# crop it down to just the right side.
CROP = (106, 0, 426, 240)
MQTT_HOST = "10.10.1.110"
MQTT_CREDS = (os.environ.get("USER", "USERNAME"), os.environ.get("PASS", "Pa55W0rd"))

FRIGATE_HOST = "http://10.10.1.110:5000"

"""
This app uses Frigate and MQTT to display a snapshot on a tiny 
display whenever someone is at my front door. 
It was kind of a pain in the ass to set up because of weird
documentation and apparently the wrath of elder gods.

This presumes you're running on a Raspberry Pi with a small ST7789 
display wired up. The following is the wiring I used. 

*NOTE*: these displays tend to use all sorts of names. For small
"pico" style boards, you're going to need a different wiring config.
Actual Raspberry Pis, however, use the SPI interface a fair bit more,
so just wiring up to GPIO ports isn't going to cut it. 

Raspberry Pis have two SPI channels 
(visible as `/dev/spidev0.0` and `/dev/spidev0.1`) We're going to want to 
use SPI 0.0. This means you want to use a few very specific pins. 
See the `SPI0_*` listed below. The other GPIO pins can go to any other
GPIO port depending on your desire for clean wiring. 

Wiring:

    st7789           pi
    ---              ---
    vcc -> purple -> 1 (3v3)
    gnd -> white  -> 6 (Ground)
    din -> green  -> 19 (GPIO10 SPI0_MOSI)
    clk -> orange -> 23 (GPIO11 SPI0_SCLK)
    cs  -> yellow -> 24 (GPIO08  SPI0_CE0)
    dc  -> blue   -> 21 (GPIO09 SPI0_MISO)
    rst -> brown  -> 22 (GPIO25)
    bl  -> gray   -> 33 (GPIO33)

    
"""


def show_img(camera, attention=2):
    """Show the latest snapshot from frigate for this camera"""
    log.debug(f"Getting image for {camera}")
    # fetch the image from my local Frigate server
    response = requests.get(f"{FRIGATE_HOST}/api/{camera}/latest.jpg?h=240&bbox=1")
    if response.status_code != 200:
        log.error(f"Bad status: {response.status_code}")
        return
    # convert the stream to an indexable object
    img = Image.open(BytesIO(response.content))
    # My camera generates an image larger than we need, crop it down
    # to just the right hand side, since that's the interesting bit.
    cropped = img.crop(CROP).resize((WIDTH, HEIGHT))
    log.info(f"""Woof: {camera}:: {time.strftime("%D %T")}""")
    log.debug(f"Woof: Image format: {img.format}, cropped to {cropped.size}")
    if display:
        # `display()` REALLY wants a PIL object. You could rewrite
        # it to take a Wand object, I suppose, but meh...
        display.display(cropped)
        # Don't get your hopes up, this is a boolean value.
        display.set_backlight(1)
        # Long enough for me to notice and squint at it to see if
        # it's worth paying attention to.
        time.sleep(attention)
        display.set_backlight(0)
    else:
        cropped.show()


def on_connect(client, _userdata, _flags, _rc):
    """Get all the events, we can parse out the more interesting ones"""
    log.info("Connected to MQTT, subscribing...")
    client.subscribe("frigate/events")


def on_message(client, _userdata, msg):
    """Run the gauntlet to see if we have something worth barking about"""
    payload = json.loads(msg.payload)
    # Either get the "before" or "after". After usually has the info about the image.
    after = payload.get("after")
    if after:
        log.debug(
            f"""Got message {after.get("label","")}, {after.get("current_zones")}"""
        )
        camera = after["camera"]
        if after["label"] == "person" and after["has_snapshot"]:
            # only bark if we can see someone.
            attention = 0
            if "fido" in after.get("current_zones"):
                attention = 2
            if "front_door" in after.get("current_zones"):
                attention = 10
            if camera == "living_room" and not attention:
                log.debug("it's not that interesting")
                return
            log.debug("It's interesting...")
            show_img(camera, attention)


# main
log = logging.getLogger("fido")
logging.basicConfig(
    level=getattr(logging, os.environ.get("PYTHON_LOG", "ERROR").upper(), None)
)
log.info("Starting up...")
display = ST7789(
    port=0,
    cs=0,
    rst=25,
    dc=9,
    backlight=13,
    width=WIDTH,
    height=HEIGHT,
    rotation=0,
    spi_speed_hz=60 * 1000 * 1000,
)
# NOTE: do not do a `display.reset()` here. One has already been
# called and it may prevent the display from showing anything.
log.info("Turning off display")
display.set_backlight(0)
# log.info("Pulling a test image")
# show_img("living_room")

log.info(f"Starting up MQTT {MQTT_CREDS}")
client = mqtt.Client()
client.scr = display
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(MQTT_CREDS[0], MQTT_CREDS[1])
client.connect(host=MQTT_HOST)

# Yep, this should absolutely use greelet or some other threading library.
# It doesn't because this is a crap program.
client.loop_forever()
