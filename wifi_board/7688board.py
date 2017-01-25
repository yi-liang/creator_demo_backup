"""
This programme will be running on a 7688 Duo board to:
(1) Read the control of the button which is connect to the 7688 board via pins;
(2) when the button is pressed, switch on or off the conveyor power which is also
    connected to the 7688 board via pins;
(3) Update the status of awa object(digital output state)

Hardware setup:
7688 duo board, conveyor power, button
two jumper wires from the button should be connected to a 3v3 pin and a Gpio pin(0) on 7688 duo board:
three jumper wires from the conveyor power should be connected to a GND and a Gpio(16) to control the power,
and another Gpio(17) to read the status of the power.

To run the programme:
python3 <identity> <secret> <timer>
<timer> is optional, if run with the timer argument, when the button is pressed,
the conveyor power will be turned on for <timer> seconds then turn off.
If run without the timer argument, pressing the button will turn on/off the conveyor power

"""

import mraa  # library installed by default on 7688 board
from time import sleep
from awaclient import Awaclient
from sys import argv

PIN_HIGH = 1
PIN_LOW = 0


class Wifiboard():

    def __init__(self, identity, secret, timer=None):

        # pin to read the button control
        self.pin_button = mraa.Gpio(0)
        self.pin_button.dir(mraa.DIR_IN)

        # pin to control the conveyor power
        self.pin_power = mraa.Gpio(16)
        self.pin_power.dir(mraa.DIR_OUT)
        self.pin_power.write(0)

        # pin to read the conveyor power status
        self.power_status = mraa.Gpio(17)
        self.power_status.dir(mraa.DIR_IN)

        # awa client
        port = 6003
        ipc_port = 6004
        self.awaclient = Awaclient(port, ipc_port, identity, secret)

        # timer
        self.timer = timer

    def start_awa(self):
        """
        Start awa client and create object/instance Digital Input State
        """
        self.awaclient.start_client("7688board")
        self.awaclient.create_object("--objectID=3200 --objectName='Digital Input' --resourceID=5500 --resourceName='Digital Input State' --resourceType=boolean --resourceInstances=single --resourceRequired=optional --resourceOperations=r")
        self.awaclient.create_resource("/3200/0")
        self.awaclient.create_resource("/3200/0/5500")

    def power_switch(self):
        """
        Turn on or off the conveyor power and update the awa object status
        (the pin to control the conveyor power stays low,
        when it raises to high, then back to low, the power will be switched.)
        """
        self.pin_power.write(PIN_HIGH)
        sleep(0.1)
        self.pin_power.write(PIN_LOW)
        print("power switch")
        print("status ", self.power_status.read())

        # Update the awa resource status
        if self.power_status.read() == PIN_HIGH:
            self.awaclient.set_resource("/3200/0/5500", True)
            if self.timer != None:
                self.timer_run()
        elif self.power_status.read() == PIN_LOW:
            self.awaclient.set_resource("/3200/0/5500", False)

    def timer_run(self):
        """
        If run in the timer mode (configured the optional argument timer),
        then turn on the conveyor for <timer> secondes and then turn it off
        """
        print("running ...")
        clock = self.timer
        for i in range(self.timer):
            sleep(1)
            print(str(clock) + " seconds")
            clock -= 1
        self.pin_power.write(PIN_HIGH)
        sleep(0.1)
        self.pin_power.write(PIN_LOW)
        print("power switch off")
        self.awaclient.set_resource("/3200/0/5500", False)

    def run(self):
        """
        starting point
        starts the awa and waits for the button control
        """
        self.start_awa()
        print("Ready")
        while True:
            sleep(0.5)
            if self.pin_button.read() == PIN_HIGH:
                self.power_switch()

if __name__ == "__main__":

    print(argv)
    if len(argv) < 3:
        raise Exception("missing identity/secret, run 'python3 <identity> <secret>'")
    identity = argv[1]
    secret = argv[2]
    try:
        timer = int(argv[3])
    except:
        timer = None
    wifi_board = Wifiboard(identity, secret, timer)
    wifi_board.run()

