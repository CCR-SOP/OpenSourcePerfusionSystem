# -*- coding: utf-8 -*-
""" Example to show basic usage of a DC pump including retrieving past actions

Assumes that the test configuration folder contains a config
"hardware.ini" with a channel called "Dialysate Inflow"

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
from pyPerfusion.Sensor import Sensor


logger = logging.getLogger()
PerfusionConfig.set_test_config()
utils.setup_stream_logger(logger, logging.DEBUG)

SYS_HW.load_hardware_from_config()

name = 'Dialysate Inflow'
try:
    sensor = Sensor(name=name)
    sensor.read_config()
except PerfusionConfig.MissingConfigSection:
    print(f'Could not find sensor called {name} in sensors.ini')
    SYS_HW.stop()
    raise SystemExit(1)

sensor.start()
reader = sensor.get_reader()
sensor.hw.start()
sensor.hw.set_output(2.0)
print('Setting output to 2V, sleeping 2 seconds')
sleep(2)
sensor.hw.set_output(1.0)
print('Setting output to 1V, sleeping 2 seconds')
sleep(2)

ts, last_samples = reader.retrieve_buffer(5000, 5)
for ts, samples in zip(ts, last_samples):
    print(f'At time {ts}: output was set to {samples}')

sensor.stop()
sensor.hw.stop()
print('stopped sensor')
for thread in enumerate():
    print(thread.name)
