from time import sleep
from pathlib import Path

from pyPerfusion.HWAcq import HWAcq
from pyPerfusion.SensorStream import SensorStream


acq = HWAcq(10)
sensor = SensorStream('test', 'ml/min', acq)

sensor.open(Path('./__data__'), Path('2020-09-14'))
sensor.start()
sleep(10)
sensor.stop()
