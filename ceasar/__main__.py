import paho.mqtt.client as client
import paho.mqtt.publish as publish
import json
import requests
import logging
import os
import time
import base64

from io import BytesIO
from PIL import Image

# My display is 1.2 inches
WIDTH = 320
HEIGHT = 240
# My camera makes a larger image than we need, so
# crop it down to just the right side.
CROP = (106, 0, 426, 240)
MQTT_HOST = os.environ.get("MQTT_HOST", "10.10.1.110")
MQTT_USER = os.environ.get("MQTT_USER", "username")
MQTT_PASS = os.environ.get("MQTT_PASS", "Pa55W0rd")
MQTT_PUB = os.environ.get("MQTT_PUB", "fido/image")
FRIGATE_HOST = os.environ.get("FRIGATE_HOST", "http://10.10.1.110:5000")

"""
So, circuitPython doesn't handle JPG images, which is annoying.
This program listens on MQTT, for any interesting events, fetches the image,
crops it, and sends it back out via MQTT to be picked up by the Pico with a display
that sits on my desk.

The pico could absolutely do most of this, except that Frigate only generates JPGs
and... well... here we are.
"""


def get_img(camera) -> bytes:
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
    cropped = img.crop(CROP).resize((WIDTH, HEIGHT)).tobitmap()
    log.info(f"""Woof: {camera}:: {time.strftime("%D %T")}""")
    log.debug(f"Woof: Image format: {img.format}, cropped to {cropped.size}")
    return cropped.tobytes()


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
        # if after["label"] == "person" and
        if after["has_snapshot"]:
            # only bark if we can see someone.
            attention = 1
            """
            if "fido" in after.get("current_zones"):
                attention = 2
            if "front_door" in after.get("current_zones"):
                attention = 10
            if camera == "office":
                attention = 10
            if camera == "living_room" and not attention:
                log.debug("it's not that interesting")
                return
            # """
            log.debug("It's interesting...")
            img_bytes = get_img(camera)
            msg = json.dumps(
                {"img": base64.b64encode(img_bytes).decode(), "attention": attention}
            )
            publish.single(
                "fido/image",
                payload=msg,
                hostname=MQTT_HOST,
                auth={"username": MQTT_USER, "password": MQTT_PASS},
            )
            log.debug("Published image....")


# main
log = logging.getLogger("fido")
logging.basicConfig(
    level=getattr(logging, os.environ.get("PYTHON_LOG", "ERROR").upper(), None)
)
log.info("Starting up...")

log.info(f"Starting up MQTT {MQTT_USER}:{MQTT_PASS}@{MQTT_HOST}")
client = client.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(host=MQTT_HOST)

# Yep, this should absolutely use greelet or some other threading library.
# It doesn't because this is a crap program.
client.loop_forever()
