# -*- coding: utf-8 -*-
""" Simple test program for demonstrating basic use of  AO classes,
    including pyAO_NIDAQ. Requires NIDAQ hardware with AO

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
import logging

import pyPerfusion.utils as utils
from pyHardware.pyAO_NIDAQ import NIDAQAODevice
import pyHardware.pyAO as pyAO
import pyPerfusion.PerfusionConfig as PerfusionConfig


PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)

dev = NIDAQAODevice()
dev.cfg = pyAO.AODeviceConfig(name='Dev1Output')
dev.read_config()
channel_names = list(dev.ao_channels)
ao_channel = dev.ao_channels[channel_names[0]]

output_type = pyAO.DCOutput()
output_type.offset_volts = 0.5
print(f'Setting output to {output_type.offset_volts}')
ao_channel.set_output(output_type)
print('Sleeping for 5 seconds')
sleep(5)
output_type.offset_volts = 2
print(f'Setting output to {output_type.offset_volts}')
ao_channel.set_output(output_type)
print('Sleeping for 5 seconds')
sleep(5)
output_type.offset_volts = 0.0
print(f'Setting output to {output_type.offset_volts}')
ao_channel.set_output(output_type)

print('closing device')
dev.close()
