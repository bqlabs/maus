import time
import smbus
from hardware.pca9865.pca9865 import ServoController
from hardware.bno055.bno055 import Inclinometer
from control.kinematics.kinematics import MausKinematics
import control.octosnake.octosnake as octosnake


class Maus(object):
    
    def __init__(self, name='maus', i2c_bus=0, servo_trims=[0, 0, 0, 0, 0], servo_pins=[8, 9, 10, 11, 4], pca9865_address=0x40, bno055_address=0x29):
        
        #Configuration
        self._name = name
        self._i2c_bus = i2c_bus
        self._servo_trims = servo_trims
        self._servo_pins = servo_pins
        self._pca9865_address = pca9865_address
        self._bno055_address = bno055_address
    
        #Setting up hardware
        self._bus = smbus.SMBus(self._i2c_bus)
        if not self._bus:
            raise Exception('I2C bus connection failed!')

        self.control = ServoController(self._bus, self._pca9865_address)
        self.sensor = Inclinometer(self._bus, self._bno055_address)

        #Setting up OctoSnake
        self.osc = []
        self.osc.append(octosnake.Oscillator())
        self.osc.append(octosnake.SemiSine())
        self.osc.append(octosnake.Oscillator())
        self.osc.append(octosnake.SemiSine())
        self.osc.append(octosnake.Oscillator())

        self.osc[1].ref_time = self.osc[0].ref_time
        self.osc[2].ref_time = self.osc[0].ref_time
        self.osc[3].ref_time = self.osc[0].ref_time
        self.osc[4].ref_time = self.osc[0].ref_time

        #Setting up PyKDL
        self.ik = MausKinematics()

        #Setting up servo controller
        for i in range(len(self._servo_pins)):
            self.control.addServo(self._servo_pins[i], self._servo_trims[i])

        self.control.servos[self._servo_pins[1]].reverse = True
        self.control.servos[self._servo_pins[3]].reverse = True

    def run(self):
        left_x_amp = 10		#millimeters
        right_x_amp = 20	#millimeters
        z_amp = 30		#millimeters
        swing_amp = 70		#degrees
        T = 1000		#milliseconds

        period = [T, T, T, T, T]
        amplitude = [left_x_amp, z_amp, right_x_amp, z_amp, swing_amp]
        offset = [-20, -75, -20, -75, 0]
        phase = [0, 90, 180, 270, 335]

        for i in range(len(self.osc)):
            self.osc[i].period = period[i]
            self.osc[i].amplitude = amplitude[i]
            self.osc[i].phase = phase[i]
            self.osc[i].offset = offset[i]


        while True:
            try:
                roll_data=self.sensor.getRoll()
                for i in range(len(self.osc)):
                    self.osc[i].refresh()

                left_joints = self.ik.getJoints(self.osc[0].output, 0, self.osc[1].output-roll_data/7)
                right_joints = self.ik.getJoints(self.osc[2].output, 0, self.osc[3].output+roll_data/7)
                self.control.move(self._servo_pins[0], left_joints[0])
                self.control.move(self._servo_pins[1], right_joints[0])
                self.control.move(self._servo_pins[2], left_joints[1])
                self.control.move(self._servo_pins[3], right_joints[1])
                self.control.move(self._servo_pins[4], self.osc[4].output-0.5*roll_data)

            except IOError:
                self._bus = smbus.SMBus(self._i2c_bus)

    #def run(self):
    #def walk_backwards(self):
    #def turnLeft(self):
    #def turnRight(self):
    #def jump(self):

maus = Maus(servo_trims=[-15, 8, 0, -18, 21])
maus.run()