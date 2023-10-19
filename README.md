# Video Fido

> "We do these things not because they are easy, but because we thought they would be easy." 
> 
> _Programmers credo_

This is a dumb little app I wrote to use an old Raspberry Pi 3B, a cheap [st7789 screen](https://www.amazon.com/2inch-IPS-LCD-Display-Module/dp/B082GFTZQD) and a pre-exsting [Frigate](https://github.com/blakeblackshear/frigate) and [MQTT](https://mqtt.org/) setup in order to let me know if someone is at the front door.

As with a lot of these sorts of projects, it was a definite "learning experience".

## What's it do?

It listens for an event indicating a camera spotted someone, and displays the photo on it's screen for about 10 seconds.

That's it. I have it set up so that it's mostly invisible to me so I know if I need to go answer the door or if I can gleefully ignore whoever.

## Isn't this a solved problem?

Yes, yes it is. There are lots of better, fancier, smoother things out there. This is cheap and hacky and private. 

## Lessons learned

* Device manufacturers love to give things almost the standardized names. 

* SPI != GPIO, particularly when dealing with a real Raspberry Pi vs a Pico board. (Please don't remind me that
even if you can power up multiple displays off a Pico, you've only got one frame buffer.)

* Things are easier than you think, unless they're very hard indeed.

## System Requirements

* Make sure your Pi has GPIO and SPI enabled using `raspi_config`
* apt install rpi.gpio, python3-spidev

## wiring

I included a wiring chart in the code, but since you're here:

|st7789 |   | pi|
|-------|---|---|
|vcc | purple | 1 (3v3)|
|gnd | white  | 6 (Ground)|
|din | green  | 19 (GPIO10 `SPI0_MOSI`)|
|clk | orange | 23 (GPIO11 `SPI0_SCLK`)|
|cs  | yellow | 24 (GPIO08 `SPI0_CE0`)|
|dc  | blue   | 21 (GPIO09 `SPI0_MISO`)|
|rst | brown  | 22 (GPIO25)|
|bl  | gray   | 33 (GPIO33)|

*Note* for anything other than the `SPI0_*` pins, you can use any other appropriate power/GPIO pin you want. Just update the code for that line.

_many wires were fiddled to bring you this chart_

## Do I have to run this as root? 

yes. The libraries directly access /dev/mem and a number of other deeply protected devices.

## Why aren't you using python project.yaml like a modern person?

Because I'm old. 

## Your code is not elegant.

Who are you, Henry Henderson? 
Look, this is a crap project I wrote to scratch an itch. I'm posting it because otherwise I'd forget about it and maybe someone else might find it useful. It's not going on my resume.