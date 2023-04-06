from machine import Pin, SPI, I2C, ADC
from helpers.sh1106 import SH1106_I2C
from helpers.ads1x15 import ADS1015
from helpers import math_helpers
from helpers import graphics
from helpers.nrf24L01 import NRF24L01
from helpers.state import State
import framebuf
import ustruct as struct
import time
import _thread
# RASBPERRY PI PICO RF TRANSMITTER CONSISTING OF:
# - 2 analog joysticks for drone movement# - 1 analog PS2 joystick for camera movement (to be added in future)# - sh1106 128x64 oled display
# - ads1115 A/D converter for additional analog inputs
# - some switches and buttons for additional control (functionality to be discussed)
# offsets will be read from file
status = State()
status = status.Offline
lock = _thread.allocate_lock()
# YAW
yaw = { 'name': 'YAW',
        'output': 0,
        'channel': 0,
        'old': 0,
        'offset': 5,
        'raw_min': 210,
        'raw_max': 1466,
        'map_min': 20,
        'map_max': -20}

# ALTITUDE
alt = { 'name': 'ALT',
        'output': 0,
        'channel': 1,
        'old': 0,
        'offset': 5,
        'raw_min': 197,
        'raw_max': 1485,
        'map_min': 0,
        'map_max': 100 }

# PITCH
pitch = {'name': 'PITCH',
        'output': 0,
        'channel': 2,
        'old': 0,
        'offset': 5,
        'raw_min': 150,
        'raw_max': 1518,
        'map_min': -50,
        'map_max': 50 }

# ROLL
roll = {'name': 'ROLL',
        'output': 0,
        'channel': 3,
        'old': 0,
        'offset': 5,
        'raw_min': 141,
        'raw_max': 1530,
        'map_min': 50,
        'map_max': -50 }

# GIMBAL SETTINGS
threshold = 5 

# JOYSTICK SETTINGS
joy_threshold = 150
menu_level = 0
menu_option = 0; last_clk_state = 0

#NRF SETTINGS
myPins = {"spi": 0, "miso": 4, "mosi": 3, "sck": 2, "csn": 5, "ce": 6}
pipes = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
led = Pin(25, mode=Pin.OUT)
csn = Pin(myPins["csn"], mode=Pin.OUT)
ce = Pin(myPins["ce"], mode=Pin.OUT)
nrf_timeout = 100
command = 0
#buff = graphics.mdrone
mdrone_graphic = framebuf.FrameBuffer(graphics.mdrone, 128, 64, framebuf.MONO_HLSB)
#buff = graphics.overlay
overlay_graphic = framebuf.FrameBuffer(graphics.overlay, 128, 64, framebuf.MONO_HLSB)
#buff.clear()

calibration_options = [
    'Roll offset',    
    'Pitch offset',
    'Yaw offset',
    'Throttle offset'
]
##### COMMS ##############################################
i2c = I2C(0, sda=Pin(8), scl=Pin(9))
nrf = NRF24L01(SPI(0, sck=Pin(2), miso=Pin(4), mosi=Pin(3)), csn, ce, channel=100, payload_size=24)
nrf.open_tx_pipe(pipes[0])
nrf.open_rx_pipe(1, pipes[1])
nrf.stop_listening()
##########################################################

##### ADC ################################################
adc_x = ADC(27)
adc_y = ADC(26)
joy_x = {'channel': adc_x,
         'old': 0,
         'output': 0,
         'threshold': 150,
         'min': -10,
         'max': 10}

joy_y = {'channel': adc_y,
         'old': 0,
         'output': 0,
         'threshold': 150,
         'min': -10,
         'max': 10}
##########################################################

##### ADC(ADS) ###########################################
ads = ADS1015(i2c, address=72, gain=1)
##########################################################

##### ENCODER ############################################
en_sw = Pin(22, Pin.IN, Pin.PULL_UP)
en_dt = Pin(21, Pin.IN)
en_clk = Pin(20, Pin.IN)

##### OLED DISPLAY########################################
LCD = SH1106_I2C(128, 64, i2c) #OLED object
LCD.rotate(True)
##########################################################

##### CUSTOM FUNCTIONS ###################################

def _read_adc(joy: dict):
    """
    Read internal adc channel for joystick position
    This joystick is steering a gimbal with camera mounted under the drone.

    Keyword arguments:
    joy -- joystick dict with channel which we want to read
    """
    if ('channel' not in joy):
        return -1
    reading = joy["channel"].read_u16()
    if(abs(reading - joy['old']) > joy['threshold']):
        joy['old'] = reading
        joy['output'] = math_helpers.map(reading, 352, 65535, joy['max'], joy['min'])

def _read_ads(data):
    lock.acquire()
    raw = ads.read(rate=1, channel1=data['channel'])
    if abs(raw - data['old']) > threshold:
        data['old'] = raw
        data['output'] = math_helpers.map(raw + data['offset'], data['raw_min'], 
                               data['raw_max'], data['map_min'], data['map_max']) #ustawić jeszcze przełączane zakresy
    lock.release()
    time.sleep_ms(3)
    return raw

def _read_all():
    _read_ads(roll)
    _read_ads(pitch)
    _read_ads(yaw)
    _read_ads(alt)
    if _read_adc(joy_x) == -1 : joy_x['output'] = -1  
    if _read_adc(joy_y) == -1 : joy_y['output'] = -1

def _showAnimation(delay):
    for i in range (63):
        LCD.fill_rect(0, 0, 128, i, 0)
        LCD.show()
        time.sleep_ms(delay)

def _menu(mainMenuText:str):
    global menu_level, roll, pitch, yaw, alt, joy_x, joy_y
    _read_all()
    #_nrf_thread()
     # zeby nie blokowac watku
    if(menu_level == 0):
        _showMainScreen(mainMenuText)
    elif(menu_level == 1):
        _showDiagMenu(roll['output'], pitch['output'], yaw['output'],alt['output'], joy_x['output'], joy_y['output'])
    elif(menu_level == 2):
        lock.acquire()
        roll['offset'] = menu_option * 5
        raw = roll['old']
        lock.release()
        _showCalibrationMenu(roll, raw)
    elif(menu_level == 3):
        lock.acquire()
        pitch['offset'] = menu_option * 5
        raw = pitch['old']
        lock.release()
        _showCalibrationMenu(pitch, raw)
    elif(menu_level == 4):
        lock.acquire()
        yaw['offset'] = menu_option * 5
        raw = yaw['old']
        lock.release()
        _showCalibrationMenu(yaw, raw)
    elif(menu_level == 5):
        lock.acquire()
        alt['offset'] = menu_option * 5
        raw = alt['old']
        lock.release()
        _showCalibrationMenu(alt, raw)
    elif(menu_level == 6):
            #tutaj zrobić zapis do pliku zaktualizowanych wartości offsetów
        menu_level = 0

def _showMainScreen(status: str):
    LCD.fill_rect(0, 11, 128, 53, 0) # clearing everything below overlay
    LCD.text('STATUS:', 0, 13, 1)
    LCD.text(status, 0, 45, 1)
    LCD.show()

def _showDiagMenu(roll, pitch, yaw, alt, x, y):
    LCD.fill_rect(0, 11, 128, 53, 0) # clearing everything below overlay
    LCD.text('Roll: Pitch: ', 0, 13)
    LCD.text(f'{roll}      {pitch}', 0, 21)
    LCD.text('Yaw:  Alt:', 0, 30)
    LCD.text(f'{yaw}     {alt}', 0, 38)
    LCD.text('X:  Y:', 0, 47)
    LCD.text(f'{x}   {y}', 0, 55)
    LCD.show()

def _showCalibrationMenu(data, raw):
    LCD.fill_rect(0, 11, 128, 53, 0)
    LCD.text(f'{data["name"]} CALIB:', 0, 13)
    LCD.text('Raw:   Map:', 0, 25)
    LCD.text(f'{raw}    {data["output"]}', 0, 33) # tutaj wartosc odczytana z przetwornika
    LCD.text('Raw+Off: Offset:', 0, 43)
    LCD.text(f'{raw + data["offset"]}      {menu_option * 5}', 0, 52) # tutaj wartosc odczytana + offset
    LCD.show()

def _sw_callback(pin):
    global menu_level, menu_option
    menu_level += 1
    menu_option = 0

def _rot_callback(pin):
    global menu_option, last_clk_state
    clk = en_clk.value()
    if(clk != last_clk_state):
        if(en_dt.value() != clk):
            menu_option +=1
        else:
            menu_option -=1
    last_clk_state = clk

def _nrf_thread():
    global roll, pitch, yaw, alt, command
    while True:
        nrf.stop_listening()
    #nadajemy wiadomosc
        lock.acquire()
        #print(f'sending: {roll["output"]}, {pitch["output"]}, {yaw["output"]}, {alt["output"]}')
        try:
            nrf.send(struct.pack('iiiii', command, int(roll["output"]), int(pitch["output"]), int(yaw["output"]), int(alt["output"])))
        except OSError:
            pass
        lock.release()
    #odbieramy wiadomosc
        nrf.start_listening()
        start_time = time.ticks_ms()
        timeout = False
        while not nrf.any() and not timeout:
            if time.ticks_diff(time.ticks_ms(), start_time) > 100:
                timeout = True
        if timeout:
            lock.acquire()
            command = 0
            lock.release()
            continue
        # a response has been received
        lock.acquire()
        response = struct.unpack("ii", nrf.recv())
        command = int(response[0])
        lock.release()
        #print ("response:", response)

en_sw.irq(trigger=Pin.IRQ_FALLING, handler=_sw_callback)
en_clk.irq(trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=_rot_callback, hard= True)
##########################################################

# GOTOWE
# LCD.fill(0)
# LCD.blit(mdrone_graphic, 0, 0)
# LCD.text("ver 0.1.0", 0, 56)
# LCD.show()
# _showAnimation(50)
command = 0
LCD.fill(0)
LCD.blit(overlay_graphic, 0, 0) #graphic overlay
LCD.fill_rect(111, 2, 7, 6, 1) # filling battery gauge (14 is max)
LCD.text('X', 10, 1) # signal strength
LCD.show()
_thread.start_new_thread(_nrf_thread, ())
while True:
    if(status == State.Offline):
    # 1) Try to connect to drone
    # 2) if not armed gain access to menu, show some drone info
    # 3) if armed disable menu, activate flight screen
    # (show takeoff options, show speed selected) 
    # IF NOT ARMED OR NO CONNECTION
    # Menu access
        _menu('Connecting')
        if command == 1: status = State.Connected

    if(status == State.Connected):
        _menu('Connected')
        if command == 0 : status = State.Offline
        elif command == 2 : status = State.Armed


