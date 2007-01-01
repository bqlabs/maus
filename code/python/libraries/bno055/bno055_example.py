import smbus
from bno055 import Inclinometer
import time

bus = smbus.SMBus(0)

device_address = 0x29

if not bus:
    raise Exception('I2C bus connection failed!')

sensor=Inclinometer(bus, device_address)

while True:
    print 'Pitch: ', sensor.get_pitch()
    print 'Roll: ', sensor.get_roll()     
    print 'Yaw: ', sensor.get_yaw()     
    time.sleep(0.1)
