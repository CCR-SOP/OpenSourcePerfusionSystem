# -*- coding: utf-8 -*-
"""Test SensorStream with multiple strategies

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
from pathlib import Path
import logging

from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
from pyPerfusion.ProcessingStrategy import RMSStrategy, SaveStreamToFile


logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)
acq = AI(period_sample_ms=100)

sensor0 = SensorStream('test0', 'ml/min', acq)
sensor1 = SensorStream('test1', 'ml/min', acq)

rms = RMSStrategy('RMS', 5, acq.buf_len)
save_rms = SaveStreamToFile('StreamRMS', None, acq.buf_len)
save_rms.open('./__data__/test', f'{sensor0.name}_rms', rms.params)

sensor0.add_strategy(rms)
sensor0.add_strategy(save_rms)

sensor0.open(Path('./__data__/test'))
sensor1.open(Path('./__data__/test'))
sensor0.set_ch_id('0')
sensor1.set_ch_id('1')


acq.open()
acq.add_channel('0')
acq.add_channel('1')
acq.set_demo_properties('0', 1, 0)
acq.set_demo_properties('1', 2, 1)
acq.start()
sensor0.start()
sensor1.start()
print('Sleeping 4 seconds')
sleep(4)
sensor0.stop()
sensor1.stop()
acq.stop()
