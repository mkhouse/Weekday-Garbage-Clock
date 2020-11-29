# Weekday-Garbage-Clock
## About
GARBAGE CLOCK for Adafruit Matrix Portal displays current time, date, day of
week, garbage alert, and countdown to garbage day.
Requires WiFi internet access.

GARBAGE CLOCK written by Melissa House is derived from:

MOON PHASE CLOCK for Adafruit Matrix Portal: displays current time, lunar
phase and time of next moonrise or moonset. Requires WiFi internet access.
Original MOON PHASE CLOCK Written by Phil 'PaintYourDragon' Burgess for
Adafruit Industries.
MIT license, all text above must be included in any redistribution.

BDF fonts from the X.Org project.

## Inspiration
This project started with Adabox 016:
https://learn.adafruit.com/adabox016/introduction
And the Adafruit Matrix Portal. (Starter kit is available at Adafruit, but may not be in stock.)
https://www.adafruit.com/product/4812

Our garbage pickup arrives between 7:30am and 8:00am Wednesday mornings. Because we
live in bear country, we have a little locked room off the side of the garage for our
garbage. If the bears smell garbage they will try to break in, and the door is bent and
covered with bear prints.

So we wait until the last minute to take the garbage out.

We try to put it in the room Tuesday before bed, but we forget a lot. This means we have
a mad scramble on Wednesday morning to get the garbage out before the pickup.

We also can't keep track of the days of the week. With quarantine, and not having a
regular schedule... who knows what day it is? Having a nice big clock with the day,
date, and time is something we've been wanting for months.

## Project
I started with the code for the Moon Phase Clock in the Adabox 016 project ideas because
I liked the matrix layout. More complicated layouts were the part of the Matrix Portal
code that made the least sense to me, and using this grid gave me a design I liked.
https://learn.adafruit.com/moon-phase-clock-for-adafruit-matrixportal

I ended up changing a lot of the code. I think I simplified it in many places, and of
course removed all of the moony bits.

I also added a demo mode, both to help with testing and to show off my work. :)

## Instructions
garbageClock.py has all of the code you need to get started. Follow the instructions
on the Adafruit site to prep the matrix portal and  install CircuitPython. Then copy the
code from garbageClock.py to code.py on your board.
https://learn.adafruit.com/adafruit-matrixportal-m4

garbageClockDebug.py is the same functionality, but with all of the print statements
I used for debugging included so you can debug with screen on your terminal app.

All of the images I used are in the bmps folder, make sure you copy these into a bmps
folder on your Matrix Portal.

## CircuityPython Libraries:
The CircuitPython Libraries I have installed in /lib on the Matrix Portal are:
* adafruit_bitmap_font
* adafruit_bus_device
* adafruit_debouncer.mpy
* adafruit_display_shapes
* adafruit_diaplay_text
* adafruit_esp32spi
* adafruit_imageload
* adafruit_io
* adafruit_lis3dh.mpy
* adafruit_matrixportal
* adafruit_requests.mpy
* adafruit_slideshow.mpy
* neopixel.mpy

(anything without an .mpy at the end is a directory, copy the whole thing)

I think a few of these libraries are not needed for this project, but if you plan to
try other projects with your Matrix Portal it's good to have all of these.

## Ideas for future work
I'm working on incorporating the buttons on the Matrix Portal to show a scrolling
message when it's time to take the garbage out that's dismissed with one of the buttons
on the Matrix Portal.

It would be possible to turn this into a daily chore clock, with different bmp images
for different tasks and multiple tasks for each day.
