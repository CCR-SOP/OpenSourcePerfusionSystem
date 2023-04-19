# -*- coding: utf-8 -*-
""" Demonstrates how to control logging messages

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
from threading import enumerate
import logging

from pyPerfusion.PerfusionSystem import PerfusionSystem
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW


logger = logging.getLogger()
PerfusionConfig.set_test_config()
utils.setup_stream_logger(logger, logging.DEBUG)

# increase PerfusionConfig to INFO level
# logging.getLogger('pyPerfusion.PerfusionConfig').setLevel(logging.INFO)

# same with Sensor
# logging.getLogger('pyPerfusion.Sensor').setLevel(logging.INFO)

# only show errors from Strategy_ReadWrite
# logging.getLogger('pyPerfusion.Strategy_ReadWrite').setLevel(logging.ERROR)

# only show logs from Arterial Gas Mixer
# utils.only_show_logs_from(['pyPerfusion.PerfusionConfig'])

# never show logs from Arterial Gas Mixer
utils.never_show_logs_from(['pyPerfusion.PerfusionConfig'])

SYS_PERFUSION = PerfusionSystem()
try:
    SYS_PERFUSION.open()
    SYS_PERFUSION.load_all()
    SYS_PERFUSION.load_automations()
except Exception as e:
    # if anything goes wrong loading the perfusion system
    # close the hardware and exit the program
    SYS_PERFUSION.close()
    raise e

SYS_PERFUSION.close()
