"""
nRF24L01 receiver
Raspberry Pi Pico and nRF24L01 module.
If an integer is received, it is acknowledged by flipping its modulo.
For more info:
www.bekyelectronics.com/raspberry-pico-nrf25l01-micropython/
"""
import ustruct as struct
import utime, neopixel
from machine import Pin, SPI
from helpers.nrf24L01 import NRF24L01
from micropython import const

# delay between receiving a message and waiting for the next message
POLL_DELAY = const(15)
# Delay between receiving a message and sending the response
# (so that the other pico has time to listen)
SEND_DELAY = const(30)

# Pico pin definition:
myPins = {"spi": 0, "miso": 0, "mosi": 3, "sck": 2, "csn": 1, "ce": 4}

# Addresses
pipes = (b'\xe1\xf0\xf0\xf0\xf0', b'\xd2\xf0\xf0\xf0\xf0')
mode = 0; roll = 0; pitch = 0; yaw = 0; alt = 0
data = []
pixel_pin = 16
pixel = neopixel.NeoPixel(Pin(pixel_pin), 1)
pixel[0] = (255, 255, 0)
pixel.write()
csn = Pin(myPins["csn"], mode=Pin.OUT)
ce = Pin(myPins["ce"], mode=Pin.OUT)
nrf = NRF24L01(SPI(0, sck=Pin(2), miso=Pin(0), mosi=Pin(3)), csn, ce, channel = 100, payload_size=24)
pixel[0] = (0, 0, 255)
pixel.write()
nrf.open_tx_pipe(pipes[1])
nrf.open_rx_pipe(1, pipes[0])
nrf.start_listening()
pixel[0] = (0, 128, 128)
pixel.write()

while True:
    if nrf.any(): # we received something
        while nrf.any():
            pixel[0] = (0, 255, 0)
            pixel.write()
            buf = nrf.recv()
        nrf.stop_listening()
        counter = struct.unpack("iiiii", buf)
        pixel[0] = (0, 0, 0)
        pixel.write()
        if counter[0] == 0 or counter[0] == 1:
            mode = 1
        elif counter[0] == 2:
            mode = 2
        try:
            nrf.send(struct.pack('ii', int(mode), int(25)))
        except OSError:
            pass
        nrf.start_listening()

