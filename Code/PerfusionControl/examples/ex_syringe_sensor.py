# -*- coding: utf-8 -*-
""" Simple test program for demonstrating basic use of  a syringe and saving
    action data

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import time

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.Sensor import Sensor
from pyHardware.SystemHardware import SYS_HW


def main():
    SYS_HW.load_all()
    # SYS_HW.load_mocks()
    SYS_HW.start()

    name = 'Methylprednisone Syringe'
    try:
        sensor = Sensor(name=name)
        sensor.read_config()
        sensor.start()
    except PerfusionConfig.MissingConfigSection:
        print(f'Could not find sensor called {name} in sensors.ini')
        SYS_HW.stop()
        exit()
        sensor = None

    reader = sensor.get_reader()
    syringe = sensor.hw

    syringe.set_target_volume(volume_ul=10_000)
    syringe.set_infusion_rate(rate_ul_min=1_000)
    syringe.infuse_to_target_volume()
    time.sleep(2.0)
    syringe.set_target_volume(volume_ul=3_000)
    syringe.set_infusion_rate(rate_ul_min=5_000)
    syringe.infuse_to_target_volume()

    syringe.close()

    time.sleep(1.0)
    ts, last_samples = reader.retrieve_buffer(5000, 5)
    for ts, samples in zip(ts, last_samples):
        print(f'{ts}: sample is {samples}')

    sensor.stop()
    SYS_HW.stop()


if __name__ == '__main__':
    utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
    PerfusionConfig.set_test_config()
    main()
