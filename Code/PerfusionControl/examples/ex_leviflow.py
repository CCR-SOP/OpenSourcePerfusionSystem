# -*- coding: utf-8 -*-
"""Test script for testing plotting of LeviFlow sensor

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem


def main():
    sensor = SYS_PERFUSION.get_sensor('Test LeviFlow')

    print(f'Converter Serial # is {sensor.hw.get_sn()}')

    print(f'Sensor type is {sensor.hw.get_sensor_type()}')

    print(f'Status is {sensor.hw.get_parameter("EquipmentStatus")}')


if __name__ == "__main__":
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)

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
