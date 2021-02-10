from time import sleep
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyHardware.pyAI import AI


dev = 'Dev4'

# test single channel, non-HW pyAI
ai = AI(period_sample_ms=100)
print('Adding channel 0')
ai.add_channel('0')
print('Removing channel 1')
ai.remove_channel('0')

print('Adding channel 0')
ai.add_channel('0')
print('Opening AI')
ai.open()
print('Starting AI')
ai.start()
sleep(2.0)
print('Retrieving data')
data, t = ai.get_data('0')
print(f'Received {len(data)} samples')
print('Stopping AI')
ai.stop()
print('Closing AI')
ai.close()

