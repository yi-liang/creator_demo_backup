"""
This programme will be running on a 7688 Duo board to:
(1) Read the control of the button which is connect to the 7688 board via pins;
(2) when the button is pressed, switch on or off the conveyor power which is also
    connected to the 7688 board via pins;
(3) Update the status of awa object(digital output state)
Hardware setup:
7688 duo board, conveyor power, button
The two jumper wires from the button, one of them should be connected to a 3v3 pin,
the other one should be connected to a Gpio pin(0) as well as the GND(via a resistor) on 7688 duo board:
The three jumper wires from the conveyor power should be connected to a GND and a Gpio(16) to control the power,
and another Gpio(17) to read the status of the power.
To run the programme:
python3 <identity> <secret> <timer>
<timer> is optional, if run with the timer argument, when the button is pressed,
the conveyor power will be turned on for <timer> seconds then turn off.
If run without the timer argument, pressing the button will turn on/off the conveyor power
"""

import atexit
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
        port = 0
        ipc_port = 12346
        self.awaclient = Awaclient(port, ipc_port, identity, secret)

        # timer
        self.timer = timer

        self.control_state = False

        atexit.register(self.exitfunc)

    def start_awa(self):
        """
        Start awa client and create object/instance Digital Input State
        (Run awa client tool as process to reduce the the dependencies for the demo)
        """
        self.awaclient.start_client("ConveyorController")
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
            self.control_state = True
            if self.timer != None:
                self.timer_run()
        elif self.power_status.read() == PIN_LOW:
            self.awaclient.set_resource("/3200/0/5500", False)
            self.control_state = False

    def recover(self):
        # was not turned off by button, turn back on
        if self.power_status.read() == PIN_LOW and self.control_state:
            self.pin_power.write(PIN_HIGH)
            sleep(0.1)
            self.pin_power.write(PIN_LOW)
            print("recovered")


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
        pin_now = self.pin_button.read()
        while True:
            self.recover()
            sleep(0.5)
            pin_next = self.pin_button.read()
            if (pin_next - pin_now) == PIN_HIGH:  # pin value raised
                self.power_switch()
            pin_now = pin_next

    def exitfunc(self):
        # when exits, turn down the power
        print("exiting ...")
        if self.power_status.read() == PIN_HIGH:
            self.pin_power.write(PIN_HIGH)
            sleep(0.1)
            self.pin_power.write(PIN_LOW)

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
