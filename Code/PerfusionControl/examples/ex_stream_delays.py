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
import logging
import time

import pyHardware.pyAI as pyAI
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.FileStrategy import StreamToFile


PerfusionConfig.set_test_config()

logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)
utils.configure_matplotlib_logging()

hw = NIDAQAIDevice()
hw_cfg = AINIDAQDeviceConfig(name='Example', device_name='Dev2',
                             sampling_period_ms=100, read_period_ms=500,
                             pk2pk_volts=5, offset_volts=2.5)
ch_cfg = pyAI.AIChannelConfig(name='test', line=0)
hw.open(hw_cfg)
hw.add_channel(ch_cfg)

sensor = SensorStream(hw.ai_channels[ch_cfg.name], 'ml/min')
sensor.add_strategy(StreamToFile('Raw', 1, 10))

sensor.open()
sensor.start()
hw.start()

STOP_PROGRAM = False


def get_last_sample():
    global strategy, last_acq
    t, sample = sensor.get_file_strategy('Raw').retrieve_buffer(0, 1)
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
hw.stop()
logger.debug('ending program')
for thread in enumerate():
    print(thread.name)
