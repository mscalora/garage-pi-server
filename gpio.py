#!/usr/bin/env python
from __future__ import print_function
# import cgi
# import cgitb; cgitb.enable()  # for troubleshooting
import sys
import time
import util
if sys.platform == 'darwin':
    from gpio_stub import GPIO
else:
    import RPi.GPIO as GPIO

relays = {
    1: 23,
    2: 22,
    3: 18,
    4: 17,
}

sensors = {
    1: 24
}

timers = {

}

ON = False
OFF = True

max_synchronous_delay = 0.10

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for relay, pin_num in relays.iteritems():
    GPIO.setup(pin_num, GPIO.OUT)
    GPIO.output(pin_num, OFF)

for sensor, pin_num in sensors.iteritems():
    GPIO.setup(pin_num, GPIO.IN)


def log_action(device, action):
    print("GPIO Device: %s Action: %s" % (device, action))


def cancel_timer(relay_num, remove_only=False):
    if relay_num in timers:
        if not remove_only:
            timers[relay_num].cancel()
        del timers[relay_num]


def pulse(relay_num, duration=0.15, log=True, async=None):
    pin = relays[relay_num]
    GPIO.output(pin, ON)
    if duration < max_synchronous_delay:
        time.sleep(duration)
        GPIO.output(pin, OFF)
    else:
        util.delay(GPIO.output, duration, [pin, OFF])
    if log:
        log_action(relay_num, "pulse for %d sec" % duration)


def off(relay_num, log=True, log_extra=""):
    pin = relays[relay_num]
    GPIO.output(pin, OFF)
    cancel_timer(relay_num)
    if log:
        log_action(relay_num, "turn off %s" % log_extra)


def on(relay_num, log=True, max_duration=None):
    pin = relays[relay_num]
    GPIO.output(pin, ON)
    cancel_timer(relay_num)
    if max_duration is not None:
        timers[relay_num] = util.delay(off, max_duration, [relay_num], {"log_extra": "via timer"})
    if log:
        log_action(relay_num, "turn on")


def toggle(relay_num, log=True, max_duration=None):
    pin = relays[relay_num]
    new_state = not bool(GPIO.input(pin))
    GPIO.output(pin, new_state)
    cancel_timer(relay_num)
    if new_state == ON and max_duration is not None:
        timers[relay_num] = util.delay(off, max_duration, [relay_num], {"log_extra": "via timer"})
    if log:
        log_action(relay_num, "toggle %s" % ('off' if new_state == OFF else 'on'))
    return new_state


def get_relay(relay_num):
    pin = relays[relay_num]
    return 'on' if GPIO.input(pin) == ON else 'off'


def set_relay(relay_num, state):
    pin = relays[relay_num]
    GPIO.output(pin, state)


def get_sensor(sensor_num):
    return GPIO.input(sensors[sensor_num])


def all_off(log=True):
    for relay_num, pin in relays.iteritems():
        GPIO.output(pin, OFF)
    if log:
        log_action("all", "turn off")


def get_all():
    return {
        "relays": {relay_num: get_relay(relay_num) for relay_num, pin in relays.iteritems()},
        "sensors": {sensor_num: get_sensor(sensor_num) for sensor_num, pin in sensors.iteritems()}
    }
