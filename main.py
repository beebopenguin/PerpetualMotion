# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO
import spidev
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus
import Slush

spi = spidev.SpiDev()
s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
             steps_per_unit=200, speed=3)

#setup the Slushengine
b = Slush.sBoard()
axis1 = Slush.Motor(0)
axis1.resetDev()
axis1.setCurrent(20, 20, 20, 20)

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 150
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
ramp = stepper(port = 0, speed = INIT_RAMP_SPEED)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////

# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    global pos
    pos = 0

    def toggleGate(self):
        global pos
        if pos == 0:
            pos = 0.5
            cyprus.set_servo_position(2, pos)
        else:
            pos = 0
            cyprus.set_servo_position(2, pos)
        print("Open and Close gate here")


    def toggleRamp(self):

        s0.set_speed(self.rampSpeed.value)

        if s0.read_switch() == 1:
            print("hi")
            s0.go_to_position(56.5)
        elif s0.get_position_in_units() == 56.5:
            axis1.goTo(0)
            print("bye")

        else:
            while(axis1.isBusy()):
                continue
            axis1.goUntilPress(0, 0, 5000) #spins until hits a NO limit at speed 1000 and direction 1


            while(axis1.isBusy()):
                continue
            axis1.setAsHome()	#set the position for 0 for all go to commands



        print("Move ramp up and down here")
        
    def auto(self):
        print("Run through one cycle of the perpetual motion machine")
        cyprus.set_servo_position(2, 0.5)
        sleep(2)
        cyprus.set_servo_position(2, 0)
        self.toggleRamp()
        while 1:
            if cyprus.read_gpio() == 6:
                cyprus.set_motor_speed(1, self.staircaseSpeed.value)
                self.toggleRamp()

                while 1:

                    if s0.read_switch() == True:
                        cyprus.set_motor_speed(1, 0)
                        s0.free_all()

    def setRampSpeed(self, speed):
        s0.set_speed(speed)
        print("Set the ramp speed and update slider text")

    def setStaircaseSpeed(self, speed):
        if self.staircase.text == "Staircase Off":
            cyprus.set_motor_speed(1, speed)
        else:
            pass
        print("Set the staircase speed and update slider text")

    def toggleStaircase(self):
        if self.staircase.text == "Staircase Off":
            cyprus.set_motor_speed(1, 0)
            self.staircase.text = "Staircase On"
        else:
            self.staircase.text = "Staircase Off"
            self.setStaircaseSpeed(self.staircaseSpeed.value)
        
    def initialize(self):
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE
    
    def quit(self):
        print("Exit")
        MyApp().stop()

sm.add_widget(MainScreen(name = 'main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
