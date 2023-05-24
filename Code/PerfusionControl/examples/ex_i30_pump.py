# -*- coding: utf-8 -*-
""" Example to show basic usage of a PuraLev i30 pump

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
from pyHardware.pyPuraLevi30 import PuraLevi30


def main():
    name = 'Test i30'
    sensor = SYS_PERFUSION.get_sensor(name)

    rpm = 500
    print(f'Setting speed to {rpm} rpm')
    sensor.hw.set_speed(rpm=rpm)
    print('Starting pump')
    sensor.hw.start()
    sleep(2.0)

    rpm = 7500
    print(f'Setting speed to {rpm} rpm')
    sensor.hw.set_speed(rpm=rpm)
    sleep(10.0)
    print('Stopping pump')
    sensor.hw.stop()

    flow_percent = 10
    print(f'Setting flow to {flow_percent}% of max')
    sensor.hw.set_flow(percent_of_max=flow_percent)
    print('Starting pump')
    sensor.hw.start()
    sleep(5.0)

    flow_percent = 50
    print(f'Setting flow to {flow_percent}% of max')
    sensor.hw.set_flow(percent_of_max=flow_percent)
    sleep(5.0)
    print('Stopping pump')
    sensor.hw.stop()



if __name__ == '__main__':
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, 'ex_dc_pump')

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
