from time import sleep

from pyHardware.pyAO_NIDAQ import NIDAQ_AO

ao = NIDAQ_AO()

ao.open(line=0, period_ms=1, dev='Dev2')
ao.set_sine(2, 2, 1)

ao.start()
sleep(5.0)
ao.halt()