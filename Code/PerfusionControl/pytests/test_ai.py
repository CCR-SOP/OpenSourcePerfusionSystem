from time import sleep
import logging

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyHardware.pyAI import AI
from pyPerfusion.utils import setup_stream_logger

logger = logging.getLogger('test_ai')
setup_stream_logger(logger, logging.DEBUG)
setup_stream_logger(logging.getLogger('pyHardware'), logging.DEBUG)


dev = 'Dev2'

# test single channel, non-HW pyAI
ai = AI(period_sample_ms=100)
logger.debug('Adding channel 0')
ai.add_channel('0')
logger.debug('Removing channel 1')
ai.remove_channel('0')

logger.debug('Adding channel 0')
ai.add_channel('0')
logger.debug('Opening AI')
ai.open()
logger.debug('Starting AI')
ai.start()
sleep(2.0)
logger.debug('Retrieving data')
data, t = ai.get_data('0')
logger.debug(f'Received {len(data)} samples')
logger.debug('Stopping AI')
ai.stop()
logger.debug('Closing AI')
ai.close()

# test single channel, HW pyAI
logger.debug('----Test NIDAQ_AI')
ai = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
logger.debug('Adding channel 0')
ai.add_channel('0')
logger.debug('Removing channel 1')
ai.remove_channel('0')

logger.debug('Adding channel 0')
ai.add_channel('0')
logger.debug('Opening AI')
ai.open(dev)
logger.debug('Starting AI')
ai.start()
sleep(2.0)
logger.debug('Retrieving data')
data, t = ai.get_data('0')
if data is None:
    logger.debug('no data from channel 0')
else:
    logger.debug(f'Received {len(data)} samples')
logger.debug('Stopping AI')
ai.stop()
logger.debug('Closing AI')
ai.close()
