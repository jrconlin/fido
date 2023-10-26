import board
import busio
import terminalio
import displayio
import os
import wifi
import ipaddress
import socketpool
import time
import json
import binascii
import circuitpython_base64 as base64
import adafruit_minimqtt.adafruit_minimqtt as MQTT

from adafruit_st7789 import ST7789

# My display is 1.2 inches
WIDTH = 320
HEIGHT = 240
# just to make things easier later, define some constants.
MQTT_HOST = os.getenv("MQTT_HOST", "10.10.1.110")
MQTT_USER = os.getenv("MQTT_USER", "username")
MQTT_PASS = os.getenv("MQTT_PASS", "Pa55W0rd")
MQTT_PUB = os.getenv("MQTT_PUB", "fido/image")

class FidoException(Exception):
    pass

"""
This app runs on a Pico W with an ST7789 screen attached. (See wiring diagram below)

*NOTE*: these displays tend to use all sorts of names. For small
"pico" style boards, you're going to need a different wiring config.
Actual Raspberry Pis, however, use the SPI interface a fair bit more,
so just wiring up to GPIO ports isn't going to cut it.

Wiring:

    st7789           pico
    ---              ---
    vcc -> purple -> 36 (3v3)
    gnd -> white  -> 18 (Ground)
    din -> green  -> 15 (GPIO11)
    clk -> orange -> 14 (GPIO10)
    cs  -> yellow -> 19 (GPIO14)
    dc  -> blue   -> 17 (GPIO13)
    rst -> brown  -> 16 (GPIO12)
    bl  -> gray   -> 20 (GPIO15)

"""


def get_pool():
    # Connect to wifi:
    ssid = os.getenv("WIFI_SSID")
    passw = os.getenv("WIFI_PASSWORD")
    # Dump the local mac address in case you want to see if it's showing
    # up in your router logs. (I saw that I was connecting, but getting a
    # bad DHCP address).
    print(u"# Mac Addr: " + binascii.hexlify(wifi.radio.mac_address).decode())
    wifi.radio.connect(ssid=ssid, password=passw)
    # Not sure why, but need to hard code the ip address info.
    if os.getenv("LOC_ADDR"):
        print(f"# Setting addr {wifi.radio.ipv4_address}")
        wifi.radio.set_ipv4_address(
            ipv4=ipaddress.ip_address(os.getenv("LOC_ADDR")),
            netmask=ipaddress.ip_address(os.getenv("LOC_MASK")),
            gateway=ipaddress.ip_address(os.getenv("LOC_GATE")),
            ipv4_dns=ipaddress.ip_address(os.getenv("LOC_DNS"))
        )
    # Test to see if you can reach the MQTT host.
    if wifi.radio.ping(ipaddress.ip_address(MQTT_HOST)):
        print("# Can access MQTT host")
    else:
        raise FidoException("Could not find MQTT Host")
    pool = socketpool.SocketPool(wifi.radio)
    return pool


def on_connect(client, _userdata, _flags, _rc):
    """Get all the events, we can parse out the more interesting ones"""
    print(f"# Connected to MQTT, subscribing to {MQTT_PUB}...")
    client.subscribe(MQTT_PUB)


def on_message(client, _userdata, msg):
    """Run the gauntlet to see if we have something worth barking about
    NOTE: on PicoW MQTT runs out of memory trying to read this message.
    """
    payload = json.loads(msg.payload)
    image = base64.b64decode(payload.img)
    print(f"# Yip!")
    display.display(image)
    # Don't get your hopes up, this is a boolean value.
    display.set_backlight(1)
    # Long enough for me to notice and squint at it to see if
    # it's worth paying attention to.
    time.sleep(payload.attention)
    display.set_backlight(0)


def get_display():
    displayio.release_displays()
    board_type = os.uname().machine
    print(f"# I am a {board_type}")
    tft_din = board.GP11  # MOSI
    tft_clk = board.GP10
    tft_cs = board.GP14
    tft_dc = board.GP13
    tft_rst = board.GP12
    tft_bl = board.GP15  # Back Light
    spi = busio.SPI(clock=tft_clk, MOSI=tft_din)

    display_bus = displayio.FourWire(
        spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst
    )

    display = ST7789(display_bus, width=320, height=240, backlight_pin=tft_bl)
    main = displayio.Group()
    display.rotation = 1
    display.show(main)

    return display


# main

display = get_display()

pool = get_pool()
user = MQTT_USER
passw = MQTT_PASS
print(f"# Connecting to... {user}:{passw}@{MQTT_HOST}")
client = MQTT.MQTT(
    broker=MQTT_HOST, username=user, password=passw, socket_pool=pool
)

client.on_connect = on_connect
client.on_message = on_message
client.connect()

print("# Connected, waiting for messages from Ceasar")
while True:
    client.loop()
