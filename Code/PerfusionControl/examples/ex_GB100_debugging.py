"""Test program to debug why GB100 turns off when changing the percentages

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep

import minimalmodbus as modbus


def get_working_status():
    global hw
    addr = 9
    val = hw.read_register(addr) == 1
    print(f'get_working_status: addr={addr}, val={val}')
    return val


def set_working_status(turn_on: bool):
    global hw
    addr = 9
    val = int(turn_on)
    print(f'set_working_status: addr={addr}, val={val}')
    hw.write_register(addr, val)


def set_total_flow(flow: int):
    global hw
    addr = 7
    print(f'set_total_flow: addr={addr}, val={flow}')
    hw.write_long(addr, flow)


def get_total_flow() -> int:
    global hw
    addr = 7
    val = hw.read_long(addr)
    print(f'get_total_flow: addr={addr}, val={val}')
    return val


def set_percent(percentage: int):
    global hw
    # channel 2 base address is 25
    addr = 25 + 6
    val = int(percentage*100)
    print(f'set_percent: addr={addr}, val={val}')
    hw.write_register(addr, val)


def get_percent() -> float:
    global hw
    # channel 2 base address is 25
    addr = 25 + 6
    val = hw.read_register(addr, number_of_decimals=2)
    print(f'get_percent: addr={addr}, val={val}')
    return val


PORT = 'COM25'
# Windows may require the port to be closed after each call
hw = modbus.Instrument(PORT, 1, modbus.MODE_RTU, close_port_after_each_call=True, debug=True)
hw.serial.baudrate = 115200
hw.serial.bytesize = 8
hw.serial.parity = modbus.serial.PARITY_NONE
hw.serial.stopbits = 1
hw.serial.timeout = 3
# these are previously unused options
hw.clear_buffers_before_each_transaction = True


working_status = get_working_status()
print(f'Gas mixer at {PORT} working status is {working_status}')

print('Turn on mixer')
set_working_status(turn_on=True)
sleep(4)
working_status = get_working_status()
print(f'Mixer working status is {working_status}')

total_flow = 50
print(f'Setting total flow to {total_flow}')
set_total_flow(total_flow)

percent = 10
print(f'Setting second channel to {percent}')
set_percent(percent)
sleep(5)

percent = 20
print(f'Setting second channel to {percent}')
set_percent(percent)
sleep(5)

print('Turn off mixer')
set_working_status(turn_on=False)
sleep(1.0)
working_status = get_working_status()
print(f'Mixer working status is {working_status}')

hw.serial.close()
