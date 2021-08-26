# -*- coding: utf-8 -*-
"""Test SensorStream with mock inputs

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

logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)
acq = AI(period_sample_ms=100)

sensor0 = SensorStream('test0', 'ml/min', acq)

sensor0.open()
sensor0.set_ch_id('0')

acq.open()
acq.add_channel('0')
acq.set_demo_properties('0', 1, 0)
acq.start()
sensor0.start()
print('Sleeping 4 seconds')
sleep(4)
sensor0.stop()
acq.stop()
