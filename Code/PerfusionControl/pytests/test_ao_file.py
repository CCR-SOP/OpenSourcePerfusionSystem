from time import sleep
import logging

from pyHardware.pyAO import AO
from pyPerfusion.utils import setup_stream_logger

logger = logging.getLogger('test_ai')
setup_stream_logger(logger, logging.DEBUG)
setup_stream_logger(logging.getLogger('pyHardware'), logging.DEBUG)

logger.debug('testing logging to a file')
ao = AO()
ao.open(line='Dummy', period_ms=0.1)
ao.set_sine(2, 2, 1)

ao.start()
sleep(5.0)
ao.halt()
