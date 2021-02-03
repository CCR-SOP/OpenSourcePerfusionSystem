from time import sleep

from pyHardware.pyAO_NIDAQ import NIDAQ_AO

ao = NIDAQ_AO()
dev = 'Dev4'
line = 0

print('Opening device')
ao.open(line=line, period_ms=1, dev=dev)
print('Closing device')
ao.close()

print('Opening device')
ao.open(line=line, period_ms=1, dev=dev)

print('Starting AO')
ao.start()
print('Setting to 2.5V')
ao.set_dc(2.5)
ao.wait_for_task()
print('Setting to 2.5V')
ao.set_dc(2.5)
ao.wait_for_task()
print('Closing device')
ao.close()
