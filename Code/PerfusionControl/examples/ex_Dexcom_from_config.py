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

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyHardware.SystemHardware import SYS_HW

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)  # add in debugging comments

SYS_HW.load_hardware_from_config()
dexcom = SYS_HW.get_hw('DEXCOM_COM6')

print(f'Read config for {dexcom.name}: ComPort={dexcom.cfg.com_port}, ',
      f'Serial # = {dexcom.cfg.serial_number}, ',
      f'Read Period (ms) = {dexcom.cfg.read_period_ms}')

