"""Test program to control GB_100 Gas Mixer based on CDI input

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
import pyPerfusion.utils as utils
from time import sleep

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
#utils.setup_file_logger(logging.getLogger(), logging.DEBUG, filename='ex_gb100')


SYS_HW.load('Arterial Gas Mixer')
SYS_HW.load('Venous Gas Mixer')
SYS_HW.start()

ha_device = SYS_HW.get_hw('Arterial Gas Mixer')
pv_device = SYS_HW.get_hw('Venous Gas Mixer')

print(f'ha device config is {ha_device.cfg}')

sample_CDI_output = [1] * 18

working_status = ha_device.get_working_status()
print(f'HA device working status is {working_status}')
working_status = pv_device.get_working_status()
print(f'PV device working status is {working_status}')

print('Turn on HA device')
ha_device.set_working_status(turn_on=True)
sleep(4)
working_status = ha_device.get_working_status()
print(f'HA device working status is {working_status}')

total_flow = 50
print(f'Setting HA total flow to {total_flow}')
ha_device.set_total_flow(total_flow)

percent = 10
print(f'Setting HA second channel to {percent}')
ha_device.set_percent_value(2, percent)

sleep(2)
ha_device.set_working_status(turn_on=True)
sleep(2)

print('Turn off HA device')
ha_device.set_working_status(turn_on=False)
working_status = ha_device.get_working_status()
print(f'HA device working status is {working_status}')

SYS_HW.stop()