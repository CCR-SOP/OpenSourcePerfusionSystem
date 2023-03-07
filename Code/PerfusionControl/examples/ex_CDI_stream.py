# -*- coding: utf-8 -*-
""" Test script to test functionality of CDI multi-variable reading/saving


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import time
from datetime import datetime

import serial

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.Sensor import Sensor
from pyHardware.SystemHardware import SYS_HW


def main():
    SYS_HW.load_hardware_from_config()
    SYS_HW.start()

    sensor = Sensor(name='Mock CDI')
    sensor.read_config()

    sensor.start()
    reader = sensor.get_reader()
    print('Sleeping for 5 seconds to collect data')
    time.sleep(5)
    ts, last_samples = reader.retrieve_buffer(5000, 5, index=3)
    for ts, samples in zip(ts, last_samples):
        print(f'{ts}: sample is {samples}')

    sensor.stop()
    SYS_HW.stop()

if __name__ == '__main__':
    utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
    PerfusionConfig.set_test_config()
    main()
