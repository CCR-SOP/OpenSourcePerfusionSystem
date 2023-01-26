# -*- coding: utf-8 -*-
""" Example to link pyAO device to stream so changes are recorded

Assumes that the test configuration folder contains a config
"hardware.ini" with a channel called "Hepatic Artery Pump"

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
from threading import enumerate
import logging

import pyHardware.pyDC as pyDC
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.FileStrategy import StreamToFile


logger = logging.getLogger()
PerfusionConfig.set_test_config()
utils.setup_stream_logger(logger, logging.DEBUG)

hw = NIDAQDCDevice()
hw.cfg = pyDC.DCChannelConfig(name='Hepatic Artery Pump')
hw.read_config()

sensor = SensorStream(hw, 'ml/min')
sensor.add_strategy(strategy=StreamToFile('Raw', 1, 10))

sensor.open()
hw.start()
sensor.start()
hw.set_output(1.0)
print('Sleeping 4 seconds')
sleep(4)
hw.set_output(2.0)
sensor.stop()
hw.stop()
print('stopped sensor')
for thread in enumerate():
    print(thread.name)
