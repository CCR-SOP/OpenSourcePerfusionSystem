from time import sleep

from pyHardware.pyAO import AO

ao = AO()
ao.open(line='Dummy', period_ms=0.1)
ao.set_sine(2, 2, 1)

ao.start()
sleep(5.0)
ao.halt()
