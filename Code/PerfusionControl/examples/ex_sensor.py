# -*- coding: utf-8 -*-
""" Demonstrates how to use Sensor class interface

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
from threading import enumerate
import logging

import pyHardware.pyAI as pyAI
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig
import pyPerfusion.Sensor as Sensor
from pyPerfusion.Strategy_ReadWrite import WriterStream
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW


logger = logging.getLogger()
PerfusionConfig.set_test_config()
utils.setup_stream_logger(logger, logging.DEBUG)

SYS_HW.load_hardware_from_config()
SYS_HW.start()
sensor = Sensor.Sensor(name='Hepatic Artery Flow')
sensor.read_config()

sensor.open()
sensor.start()
print('Sleeping 4 seconds')
sleep(4)
sensor.stop()
SYS_HW.stop()
print('stopped sensor')
for thread in enumerate():
    print(thread.name)
