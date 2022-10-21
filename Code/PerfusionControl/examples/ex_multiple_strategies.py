# -*- coding: utf-8 -*-
"""Demonstrate SensorStream with multiple strategies

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
import logging

import pyHardware.pyAI as pyAI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
from pyPerfusion.ProcessingStrategy import RMSStrategy
from pyPerfusion.FileStrategy import StreamToFile
import pyPerfusion.PerfusionConfig as PerfusionConfig

PerfusionConfig.set_test_config()

logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)
hw = pyAI.AIDevice()
dev_cfg = pyAI.AIDeviceConfig(name='HighSpeed',
                              device_name='FakeDev',
                              sampling_period_ms=25,
                              read_period_ms=250)
ch_cfg = pyAI.AIChannelConfig(name='Test Multiple Strategies', line=0)
hw.open(dev_cfg)
hw.add_channel(ch_cfg)

sensor0 = SensorStream(hw.ai_channels[ch_cfg.name], 'ml/min')

raw = StreamToFile('StreamRaw', None, hw.buf_len)
raw.open(sensor0)
rms = RMSStrategy('RMS', 5, hw.buf_len)
save_rms = StreamToFile('StreamRMS', None, hw.buf_len)
save_rms.open(sensor0)

sensor0.add_strategy(raw)
sensor0.add_strategy(rms)
sensor0.add_strategy(save_rms)

sensor0.open()

hw.start()
sensor0.start()
print('Sleeping 4 seconds')
sleep(4)
sensor0.stop()
hw.stop()
