# -*- coding: utf-8 -*-
"""Test delays in reading/writing stream data over longer time periods

During system testing, it was reported that the plots were delayed
by up to tens of seconds compared to hardware flow meter readouts

This scripts is intended to verify if the delays are the result of
reading/writing of the data directly

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from threading import Timer, enumerate
from datetime import datetime
import logging
import time

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG

dev = 'Dev2'

logger = logging.getLogger()
LP_CFG.set_base(basepath='~/Documents/LPTEST')
LP_CFG.update_stream_folder()
utils.setup_stream_logger(logger, logging.DEBUG)
utils.configure_matplotlib_logging()

ai_name = 'Analog Input'
logger.debug('creating NIDAQ_AI')
acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
sensor = SensorStream('Analog Input 1', 'Volts', acq)
logger.debug('opening sensor')
sensor.open(LP_CFG.LP_PATH['stream'])
acq.add_channel('0')
sensor.set_ch_id('0')
acq.open(dev=dev)
logger.debug('starting acquisition')
sensor.start()
acq.start()

STOP_PROGRAM = False


def get_last_sample():
    global sensor, last_acq
    sample = sensor.get_current()
    logger.debug(f'Acquired {sample}')


def stop_program():
    global STOP_PROGRAM
    logger.debug('stopping program')
    STOP_PROGRAM = True


#timer_stop = Timer(5 * 60.0, stop_program)
#timer_stop.start()
timer = Timer(1.0, get_last_sample)

while not STOP_PROGRAM:
    try:
        if not timer.is_alive():
            timer = Timer(1.0, get_last_sample)
            timer.start()
        else:
            time.sleep(0.1)
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
