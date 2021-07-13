from time import sleep
import logging

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG

dev = 'Dev1'

logger = logging.getLogger()
LP_CFG.set_base(basepath='~/Documents/LPTEST')

utils.setup_stream_logger(logger, logging.DEBUG)
acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)

sensor0 = SensorStream('test0', 'ml/min', acq)
sensor1 = SensorStream('test1', 'ml/min', acq)

sensor0.open()
sensor1.open()
sensor0.set_ch_id('0')
sensor1.set_ch_id('1')

acq.open(dev)
acq.add_channel('0')
acq.add_channel('1')
acq.start()
sensor0.start()
sensor1.start()
print('Sleeping 4 seconds')
sleep(4)
sensor0.stop()
sensor1.stop()
acq.stop()
