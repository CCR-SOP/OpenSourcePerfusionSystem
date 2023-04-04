# -*- coding: utf-8 -*-
""" Example to show basic usage of a PuraLev i30 pump

Assumes that the test configuration folder contains a config
"hardware.ini" with a section called "Test i30"

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
from threading import enumerate
import logging

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
from pyHardware.pyPuraLevi30 import PuraLevi30


logger = logging.getLogger()
PerfusionConfig.set_test_config()
utils.setup_stream_logger(logger, logging.DEBUG)

SYS_HW.load_hardware_from_config()

name = 'Test i30'

print(f'Opening pump {name}')
pump = PuraLevi30(name=name)
pump.read_config()
print(f'Config is {pump.cfg}')

rpm = 500
print(f'Setting speed to {rpm} rpm')
pump.set_speed(rpm=rpm)
print('Starting pump')
pump.start()
sleep(2.0)

rpm = 1500
print(f'Setting speed to {rpm} rpm')
pump.set_speed(rpm=rpm)
sleep(2.0)
print('Stopping pump')
pump.stop()

flow_percent = 10
print(f'Setting flow to {flow_percent}% of max')
pump.set_flow(percent_of_max=flow_percent)
print('Starting pump')
pump.start()
sleep(5.0)

flow_percent = 50
print(f'Setting flow to {flow_percent}% of max')
pump.set_flow(percent_of_max=flow_percent)
sleep(5.0)
print('Stopping pump')
pump.stop()

pump.close()

for thread in enumerate():
    print(thread.name)
