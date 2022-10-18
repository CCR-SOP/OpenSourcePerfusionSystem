# -*- coding: utf-8 -*-
"""Simple test script to test finite acquisition to SensorPoint

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import sleep

from pyHardware.pyAI_Finite_NIDAQ import AI_Finite_NIDAQ
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.FileStrategy import StreamToFile


PerfusionConfig.set_test_config()

logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)

dev = 'Dev2'
line = '0'
samples = 5
period_ms = 1000

logger.info(f'Creating AI_Finite_NIDAQ with period_ms of {period_ms}')
ai = AI_Finite_NIDAQ(period_ms=period_ms, volts_p2p=5, volts_offset=2.5, samples_per_read=samples)
sensor = SensorPoint('FiniteAcq', 'counts', ai)
logger.info(f'Opening {dev}')
ai.open(dev)
logger.info(f'Adding channel {line}')
ai.add_channel(line)
sensor.set_ch_id(line)
strategy = StreamToFile('Raw', 1, 10)
strategy.open(PerfusionConfig.get_date_folder(), sensor.name, sensor.params)
sensor.add_strategy(strategy)
sensor.open()

logger.info('opening sensor')
logger.info(f'saving data to {PerfusionConfig.get_date_folder()}')
sensor.open()

logger.info('starting acquisition')
ai.start()
sensor.start()
done = False
logger.info('acquisition started')
while not done:
    logger.info(f'waiting for {samples} to be acquired')
    sleep(1.0)
    done = ai.is_done()

logger.info('get another group of samples')
ai.start()
logger.info('acquisition started')
done = False
while not done:
    logger.info(f'waiting for {samples} to be acquired')
    sleep(1.0)
    done = ai.is_done()
logger.info('stopping sensors')
sensor.stop()
ai.close()
logger.info('Done')