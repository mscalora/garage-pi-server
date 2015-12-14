from __future__ import print_function

gpio_state = {

}

class GPIO:
    BCM = -1
    OFF = 0
    ON = 1
    OUT = -2
    IN = -3

    def __init__(self):
        pass

    @staticmethod
    def setmode(mode):
        pass

    @staticmethod
    def setwarnings(mode):
        pass

    @staticmethod
    def output(pin, state):
        global gpio_state
        print("Pin: %d State: %s" % (pin, str(state)))
        gpio_state[pin] = state

    @staticmethod
    def input(pin):
        global gpio_state
        state = gpio_state[pin] if pin in gpio_state else False
        print("Pin: %d State: %s" % (pin, str(state)))
        return state

    @staticmethod
    def setup(pin, state):
        global gpio_state
        pass
