# -*- coding: utf-8 -*-
""" Example to show basic usage of a DC pump including retrieving past actions

Assumes that the test configuration folder contains a config
"hardware.ini" with a channel called "Dialysate Inflow"

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from time import sleep
import logging
import threading

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem


def main():
    name = 'Dialysate Outflow Pump'
    sensor = SYS_PERFUSION.get_sensor(name)
    reader = sensor.get_reader()
    sensor.hw.set_output(2.0)
    print('Setting output to 2V, sleeping 2 seconds')
    sleep(6)
    sensor.hw.set_output(1.0)
    print('Setting output to 1V, sleeping 2 seconds')
    sleep(2)

    print('Retrieving actions from file')
    ts, last_samples = reader.retrieve_buffer(5000, 5)
    for ts, samples in zip(ts, last_samples):
        print(f'At time {ts}: output was set to {samples}')


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
