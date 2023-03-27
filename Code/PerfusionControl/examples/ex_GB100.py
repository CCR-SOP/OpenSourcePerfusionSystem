"""Test program to control GB_100 Gas Mixer based on CDI input

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
from time import sleep

PerfusionConfig.set_test_config()

SYS_HW.load_hardware_from_config()
ha_device = SYS_HW.get_hw('Arterial Gas Mixer')
pv_device = SYS_HW.get_hw('Venous Gas Mixer')

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

total_flow = 100
print(f'Setting HA total flow to {total_flow}')
ha_device.set_total_flow(total_flow)

percent = 30
print(f'Setting HA second channel to 30%')
ha_device.set_percent_value(2, percent)

sleep(3)
ha_device.set_working_status(turn_on=True)

print('Turn off HA device')
ha_device.set_working_status(turn_on=False)
working_status = ha_device.get_working_status()
print(f'HA device working status is {working_status}')