# -*- coding: utf-8 -*-
""" Example to show how to create a sensor stream from a saved config

Assumes that the test configuration folder contains a config
"TestAnalogInputDevice.ini" with a channel called "Flow" and a
config called "sensors.ini" with a section called "HA Flow"

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
from threading import enumerate
import logging

import pyHardware.pyAI as pyAI
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.FileStrategy import StreamToFile


logger = logging.getLogger()
PerfusionConfig.set_test_config()
utils.setup_stream_logger(logger, logging.DEBUG)

hw = NIDAQAIDevice()
hw.cfg = AINIDAQDeviceConfig(name='TestAnalogInputDevice')
hw.read_config()

sensor = SensorStream(hw.ai_channels['HA Flow'], 'ml/min')
sensor.read_config()

strategy = sensor.get_file_strategy('Stream2File')
print(strategy.cfg.name)
