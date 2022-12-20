"""

Example script to show how to read data from a Dexcom receiver using a config

[Hepatic Artery]
name = Hepatic Artery
com_port = COM1
serial_number = PG01602411
read_period_ms = 30000

Actually port value should be changed to the value of the Dexcom port


@project: Liver Perfusion, NIH
@author: John Kakareka, NIH

"""

import logging
from time import sleep

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyDexcom as pyDexcom

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)  # add in debugging comments

dexcom = pyDexcom.DexcomReceiver('Hepatic Artery')
dexcom.read_config()
print(f'Read config for {dexcom.name}: ComPort={dexcom.cfg.com_port}, ',
      f'Serial # = {dexcom.cfg.serial_number}, ',
      f'Read Period (ms) = {dexcom.cfg.read_period_ms}')
print('Attempting to read data')
dexcom.start()
for i in range(2):
      print('sleeping for 1 second')
      sleep(1.0)
      data, t = dexcom.get_data()
      print(f'Timestamp is {t}')
      print(f'Data is {data}')

dexcom.stop()
dexcom.close()
