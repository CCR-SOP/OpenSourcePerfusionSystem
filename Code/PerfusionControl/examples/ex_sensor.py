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


logger = logging.getLogger()
PerfusionConfig.set_test_config()
utils.setup_stream_logger(logger, logging.DEBUG)

hw = NIDAQAIDevice()
hw_cfg = AINIDAQDeviceConfig(name='Example', device_name='Dev2',
                             sampling_period_ms=100, read_period_ms=500,
                             pk2pk_volts=5, offset_volts=2.5)
ch_cfg = pyAI.AIChannelConfig(name='test', line=0)
hw.open(hw_cfg)
hw.add_channel(ch_cfg)

sensor = Sensor.Sensor(cfg=Sensor.SensorConfig(name='Test', hw=hw.ai_channels[ch_cfg.name]))



sensor = SensorStream(hw.ai_channels[ch_cfg.name], 'ml/min')
sensor.add_strategy(StreamToFile('Raw', 1, 10))

sensor.open()
sensor.start()
hw.start()
print('Sleeping 4 seconds')
sleep(4)
sensor.stop()
hw.stop()
print('stopped sensor')
for thread in enumerate():
    print(thread.name)
