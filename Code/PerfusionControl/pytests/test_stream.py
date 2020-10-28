from time import sleep
from pathlib import Path

from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream


acq = AI(10)
sensor = SensorStream('test', 'ml/min', acq)

sensor.open(Path('./__data__'), Path('2020-09-14'))
sensor.start()
sleep(10)
sensor.stop()
