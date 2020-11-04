from time import sleep

from pyHardware.pyAO_NIDAQ import NIDAQ_AO

ao = NIDAQ_AO()
ao.open(0, 0.1, 2, 1, 0, dev='Dev1')
ao.set_sine(2, 2, 1)

ao.start()
sleep(5.0)
ao.set_sine(1, 0.5, 0)
sleep(5.0)
ao.set_dc(0.75)
sleep(2.0)
ao.set_dc(3.33)
sleep(3.0)
ao.close()