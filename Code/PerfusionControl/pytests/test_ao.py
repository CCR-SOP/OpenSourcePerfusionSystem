from time import sleep

from pyHardware.pyAO_NIDAQ import NIDAQ_AO

ao1 = NIDAQ_AO()
ao2 = NIDAQ_AO()
dev = 'Dev4'
line = 0

print('Opening device')
ao1.open(line=line, period_ms=1, dev=dev)
print('Closing device')
ao1.close()

print('Opening device')
ao1.open(line=line, period_ms=1, dev=dev)

print('Starting AO')
ao1.start()
print('Setting to 2.5V')
ao1.set_dc(2.5)
ao1.wait_for_task()
print('Setting to 2.5V')
ao1.set_dc(2.5)
ao1.wait_for_task()
print('Closing device')
ao1.close()

print('Opening first device')
ao1.open(line=line, period_ms=1, dev=dev)
print('Opening second device')
ao2.open(line=line+1, period_ms=1, dev=dev)

print('Starting AO')
ao1.start()
ao2.start()
print('Setting first line to 2.5V, second line to 1.0V')
ao1.set_dc(2.5)
ao1.set_dc(1.0)
ao1.wait_for_task()
ao2.wait_for_task()


print('Setting first line to 2.5V, second line to sine ')
ao1.set_dc(2.5)
ao2.set_sine(volts_p2p=2, volts_offset=1, Hz=2.0)
print('pausing 2.0 seconds')
sleep(2.0)


print('Setting first line to sine, second line to sine ')
ao1.set_sine(volts_p2p=1, volts_offset=0.5, Hz=1.0)
ao2.set_sine(volts_p2p=2, volts_offset=1, Hz=2.0)
print('pausing 2.0 seconds')
sleep(2.0)


print('Closing devices')
ao1.close()
ao2.close()
