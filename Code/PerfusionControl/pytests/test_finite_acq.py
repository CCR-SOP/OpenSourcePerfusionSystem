# -*- coding: utf-8 -*-
"""Simple test script to test acquisition of finite number of samples

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import sleep

from pyHardware.pyAI_Finite_NIDAQ import AI_Finite_NIDAQ
import pyPerfusion.utils as utils


logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)

dev = 'Dev4'
line = '0'
samples = 5
period_ms = 1000

logger.info(f'Creating AI_Finite_NIDAQ with period_ms of {period_ms}')
ai = AI_Finite_NIDAQ(period_ms=period_ms, volts_p2p=5, volts_offset=2.5)
logger.info(f'Opening {dev}')
ai.open(dev)
logger.info(f'Adding channel {line}')
ai.add_channel(line)
logger.info('starting acquisition')
ai.start(samples)
done = False
print('acquisition started')
while not done:
    logger.info(f'waiting for {samples} to be acquired')
    sleep(1.0)
    done = ai.is_done()

ai.close()
logger.info('Done')