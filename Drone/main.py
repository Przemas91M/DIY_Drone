from machine import Pin, PWM, ADC, I2C
from helpers.mpu9250 import MPU9250
import time

arm = 500000 #nie dziala w przypadku moich ESC
min_duty = 1000000 #minimalny duty cycle dla ESC
max_duty = 2000000 #maksymalny duty cycle dla ESC
G = 9.80665

control = PWM(Pin(0))
control.freq(50)
pot = ADC(26)
conversion_f = 4915 / (65535)
i2c = I2C(1, scl=Pin(7), sda=Pin(6)) #I2C(1, scl=Pin(7), sda=Pin(6)) #I2C object

mpu = MPU9250(i2c)

for i in range(50):
    acc = mpu.acceleration
    temp = mpu.temperature
    gyro = mpu.gyro
    time.sleep(0.2)
#control.duty_ns(arm)
#time.sleep(3)
#print("Done.")

# while True:
#     reading = pot.read_u16() #* conversion_f
#     #mapowanie min/max wartosci sterowania
#     output = math_helpers.map(reading, 0, 65536, min_duty, max_duty)
#     #control.duty_u16(int(output))
#     control.duty_ns(output)
#     readingStr = str(output)
#     LCD.fill(0)
#     LCD.text(readingStr, 0, 0, 1)
#     LCD.show()
#     time.sleep_ms(500)
