import time
from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

if __name__ == '__main__':
    for i in range(18):
        for j in range(6):
            kit.servo[j + 10].set_pulse_width_range(1000, 2000)
            kit.servo[j + 10].angle = i * 10
        print(i * 10)
        time.sleep(1)
