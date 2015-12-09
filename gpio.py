#!/usr/bin/env python
from __future__ import print_function
# import cgi
# import cgitb; cgitb.enable()  # for troubleshooting
import sys
import time
import os
import re
if sys.platform=='darwin':
    from gpio_stub import GPIO
else:
    import RPi.GPIO as GPIO

relays = {
    1: 17,
    2: 18,
    3: 22,
    4: 23,
}

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for relay, pin in relays.iteritems():
    GPIO.setup(pin, GPIO.OUT)


def pulse(relay_num, duration=0.15, log=True):
    pin = relays[relay_num]
    GPIO.output(pin, True)
    time.sleep(duration)
    GPIO.output(pin, False)


def off(relay_num, log=True):
    pin = relays[relay_num]
    GPIO.output(pin, False)


def on(relay_num, log=True):
    pin = relays[relay_num]
    GPIO.output(pin, True)


def all_off(log=True):
    for relay, pin in relays.iteritems():
        GPIO.output(pin, False)
