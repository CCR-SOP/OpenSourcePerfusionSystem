# -*- coding: utf-8 -*-
""" Example to show sinusoidal output of a PuraLev i30 pump

Assumes that the test configuration folder contains a config
"hardware.ini" with a section called "Test i30"

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
import threading
import logging

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem


def main():
    name = 'Test Puralev Sine'
    sensor = SYS_PERFUSION.get_sensor(name)

    print('Starting pump')
    # sensor.hw.start()
    sleep(10.0)

    print('Changing frequency to 2Hz')
    sensor.hw.cfg.sine_freq = 2.0
    sleep(10.0)

    print('Stopping pump')
    sensor.hw.stop()


if __name__ == '__main__':
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, 'ex_i30_pump_sine')

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

    main()

    SYS_PERFUSION.close()
    for thread in threading.enumerate():
        print(thread.name)
