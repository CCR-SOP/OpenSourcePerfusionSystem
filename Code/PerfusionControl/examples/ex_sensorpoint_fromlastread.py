# -*- coding: utf-8 -*-
"""Test getting the data from the last acquired timestamp of SensorPoint stream


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from threading import Timer, enumerate
from datetime import datetime
import logging
import time

from pyHardware.pyAI_Finite_NIDAQ import AI_Finite_NIDAQ
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import PointsToFile

dev = 'Dev1'

logger = logging.getLogger()
LP_CFG.set_base(basepath='~/Documents/LPTEST')
LP_CFG.update_stream_folder()
utils.setup_stream_logger(logger, logging.DEBUG)
utils.configure_matplotlib_logging()

ai_name = 'Analog Input'
logger.debug('creating NIDAQ_AI')
acq = AI_Finite_NIDAQ(period_ms=100, volts_p2p=5, volts_offset=2.5, samples_per_read=2)
sensor = SensorPoint('Analog Input 1', 'Volts', acq)
logger.debug('opening sensor')

strategy = PointsToFile('StreamToFileRaw', 1, 10)
strategy.open(LP_CFG.LP_PATH['stream'], sensor.name,
              {'Sampling Period (ms)': 100, 'Data Format': 'float32',
               'Samples Per Timestamp': 2})

sensor.open()
sensor.add_strategy(strategy)
acq.open(dev=dev)
acq.add_channel('0')
sensor.set_ch_id('0')
logger.debug('starting acquisition')
sensor.start()
acq.start()

STOP_PROGRAM = False
last_acq = 0


def get_last_sample():
    global strategy, last_acq
    logger.debug(f'last read occurred at  {last_acq}')
    ts, samples = strategy.get_data_from_last_read(last_acq)
    logger.debug(f'Acquired {len(ts)} samples')
    logger.debug(f'Acquired ts = {ts}')
    if len(ts) > 0:
        last_acq = ts[-1]

def stop_program():
    global STOP_PROGRAM
    logger.debug('stopping program')
    STOP_PROGRAM = True


timer = Timer(1.0, get_last_sample)

while not STOP_PROGRAM:
    try:
        if not timer.is_alive():
            timer = Timer(5.0, get_last_sample)
            timer.start()
        else:
            time.sleep(1.0)
            acq.start()
    except KeyboardInterrupt:
        STOP_PROGRAM = True

timer.cancel()
# timer_stop.cancel()
logger.debug('stopping sensor')
sensor.stop()
acq.stop()
logger.debug('ending program')
for thread in enumerate():
    print(thread.name)
