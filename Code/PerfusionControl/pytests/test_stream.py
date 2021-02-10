from time import sleep
from pathlib import Path

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream

dev = 'Dev2'
acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)

sensor0 = SensorStream('test0', 'ml/min', acq, '0')
sensor1 = SensorStream('test1', 'ml/min', acq, '1')

sensor0.open(Path('./__data__/test'))
sensor1.open(Path('./__data__/test'))
acq.add_channel('0')
acq.add_channel('1')
acq.open(dev)
acq.start()
sensor0.start()
sensor1.start()
print('Sleeping 2 seconds')
sleep(4)
sensor0.stop()
sensor1.stop()
acq.stop()
