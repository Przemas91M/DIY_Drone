from machine import Pin, SPI
from helpers.nrf24L01 import NRF24L01
import struct
import time

# pin definition for the Raspberry Pi Pico:
myPins = {"spi": 0, "miso": 4, "mosi": 3, "sck": 2, "csn": 5, "ce": 6}
# Addresses (little endian)
pipes = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
print("NRF24L01 transmitter")
led = Pin(25, mode=Pin.OUT)
csn = Pin(myPins["csn"], mode=Pin.OUT)
ce = Pin(myPins["ce"], mode=Pin.OUT)
nrf = NRF24L01(SPI(0, sck=Pin(2), miso=Pin(4), mosi=Pin(3)), csn, ce, payload_size=24)
nrf.open_tx_pipe(pipes[0])
nrf.open_rx_pipe(1, pipes[1])
nrf.start_listening()

counter = 0

for i in range(150):
    #nadajemy wiadomosc
    nrf.stop_listening()
    led.high()
    print(f'sending: {counter}')
    try:
        nrf.send(struct.pack('iiiii', int(1),int(2),int(3),int(4),int(5)))
    except OSError:
        pass
    led.low()
    time.sleep_ms(15)
    #odbieramy wiadomosc
    nrf.start_listening()
    start_time = time.ticks_ms()
    timeout = False
    if (nrf.any()):
        led.high()
        buf = nrf.recv()
        (response) = struct.unpack('ii', buf)
        print(f'response received: {response}')
        led.low()
    time.sleep(1)