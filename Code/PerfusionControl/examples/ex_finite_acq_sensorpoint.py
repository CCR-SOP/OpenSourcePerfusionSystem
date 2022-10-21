# -*- coding: utf-8 -*-
"""Simple test script to test finite acquisition to SensorPoint

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import sleep

from pyHardware.pyAI_Finite_NIDAQ import FiniteNIDAQAIDevice, FiniteNIDAQAIDeviceConfig
import pyHardware.pyAI as pyAI
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.FileStrategy import StreamToFile


logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)
PerfusionConfig.set_test_config()

dev_cfg = FiniteNIDAQAIDeviceConfig(name='FiniteAcqSensorPoint test',
                                    device_name='Dev2',
                                    samples_per_read=5,
                                    sampling_period_ms=1000)
ch_cfg = pyAI.AIChannelConfig(name='TestChannel', line=0)

logger.info(f'Creating AI_Finite_NIDAQ with sampling_period_ms of {dev_cfg.sampling_period_ms}')
ai = FiniteNIDAQAIDevice()
logger.info(f'Opening {dev_cfg.device_name}')
ai.open(dev_cfg)
logger.info(f'Adding channel {ch_cfg.line}')
ai.add_channel(ch_cfg)

sensor = SensorPoint(ai.ai_channels[ch_cfg.name], 'counts')

strategy = StreamToFile('Raw', 1, 10)
strategy.open(sensor)
sensor.add_strategy(strategy)
sensor.open()

logger.info('opening sensor')
sensor.open()

logger.info('starting acquisition')
ai.start()
sensor.start()
done = False
logger.info('acquisition started')
while not done:
    logger.info(f'waiting for {dev_cfg.samples_per_read} to be acquired')
    sleep(1.0)
    done = ai.is_done()

logger.info('get another group of samples')
ai.start()
logger.info('acquisition started')
done = False
while not done:
    logger.info(f'waiting for {dev_cfg.samples_per_read} to be acquired')
    sleep(1.0)
    done = ai.is_done()
logger.info('stopping sensors')
sensor.stop()
ai.close()
logger.info('Done')