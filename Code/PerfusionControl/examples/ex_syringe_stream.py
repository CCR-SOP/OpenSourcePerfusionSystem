# -*- coding: utf-8 -*-
""" Simple test program for demonstrating basic use of  a syringe and saving
    action data

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
import logging

import pyPerfusion.pyPump11Elite as pyPump11Elite
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import PointsToFile


class MockPump11Elite(pyPump11Elite.Pump11Elite):
    def __init__(self, name: str):
        super().__init__(name)
        self._last_send = ''

    def send_wait4response(self, str2send: str) -> str:
        response = ''
        if str2send == 'tvolume\r':
            response = '100 ul'
        elif str2send == 'irate\r':
            response = '10 ul/min'
        return response


dev = 'COM1'
baud_rate = 9600

logger = logging.getLogger()
LP_CFG.set_base(basepath='~/Documents/LPTEST')
LP_CFG.update_stream_folder()

utils.setup_stream_logger(logger, logging.DEBUG)
syringe = MockPump11Elite(name='Example')
syringe.open(dev, baud_rate)

sensor0 = SensorPoint('test0', 'ml/min', syringe)

strategy = PointsToFile('Raw', 1, 10)
strategy.open(LP_CFG.LP_PATH['stream'], sensor0.name, sensor0.params)
sensor0.add_strategy(strategy)
sensor0.start()

syringe.set_target_volume(volume_ul=10_000)
syringe.set_infusion_rate(rate_ul_min=1_000)
syringe.infuse_to_target_volume()
syringe.close()

sensor0.stop()
sensor0.close()
