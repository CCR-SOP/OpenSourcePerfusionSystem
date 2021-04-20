from time import sleep
import logging

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyPerfusion.utils import setup_stream_logger

logger = logging.getLogger('test_ao')
setup_stream_logger(logger, logging.DEBUG)
setup_stream_logger(logging.getLogger('pyHardware'), logging.DEBUG)

ao1 = NIDAQ_AO()
ao2 = NIDAQ_AO()
dev = 'Dev2'
line = 0

logger.debug('Opening device')
ao1.open(line=line, period_ms=1, dev=dev)
logger.debug('Closing device')
ao1.close()

logger.debug('Opening device')
ao1.open(line=line, period_ms=1, dev=dev)

logger.debug('Starting AO')
ao1.start()
logger.debug('Setting to 2.5V')
ao1.set_dc(2.5)
ao1.wait_for_task()
logger.debug('Setting to 2.5V')
ao1.set_dc(2.5)
ao1.wait_for_task()
logger.debug('Closing device')
ao1.close()

logger.debug('Opening first device')
ao1.open(line=line, period_ms=1, dev=dev)
logger.debug('Opening second device')
ao2.open(line=line+1, period_ms=1, dev=dev)

logger.debug('Starting AO')
ao1.start()
ao2.start()
logger.debug('Setting first line to 2.5V, second line to 1.0V')
ao1.set_dc(2.5)
ao1.set_dc(1.0)
ao1.wait_for_task()
ao2.wait_for_task()


logger.debug('Setting first line to 2.5V, second line to sine ')
ao1.set_dc(2.5)
ao2.set_sine(volts_p2p=2, volts_offset=1, Hz=2.0)
logger.debug('pausing 2.0 seconds')
sleep(2.0)


logger.debug('Setting first line to sine, second line to sine ')
ao1.set_sine(volts_p2p=1, volts_offset=0.5, Hz=1.0)
ao2.set_sine(volts_p2p=2, volts_offset=1, Hz=2.0)
logger.debug('pausing 2.0 seconds')
sleep(2.0)


logger.debug('Closing devices')
ao1.close()
ao2.close()
