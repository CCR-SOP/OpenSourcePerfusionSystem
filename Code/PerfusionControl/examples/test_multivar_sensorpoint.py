# -*- coding: utf-8 -*-
""" Test script to test functionality of multi-variable reading/saving


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import serial

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint

COMPORT = 'COM13'


def main():

    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)  # add in debugging comments

    fake_port = serial.serial_for_url('loop://')
    cdi = pyCDI.CDIStreaming('Test CDI')
    cdi.open(fake_port, 9600)
    cdi_str = 'abc\t' + '\t'.join(str(i) for i in range(16))
    fake_port.write(bytes(cdi_str, 'ascii'))

    sensorpt = SensorPoint('multi_var', 'na', cdi)
    write_strategy = MultiVarToFile('write', 1, 17)
    sensorpt.add_strategy(write_strategy)

    ro_sensorpt = ReadOnlySensorPoint('multi_var', 'na', cdi)
    read_strategy = MultiVarFromFile('multi_var', 1, 17, 1)
    sensorpt.add_strategy(read_strategy)

    sensorpt.start()
    ro_sensorpt.start()

    data = list(range(16))
    for i in range(10):
        cdi_str = 'abc\t' + '\t'.join(str(d+i) for d in data)
        fake_port.write(bytes(cdi_str, 'ascii'))
        print(read_strategy.get_last_acq())


if __name__ == '__main__':
    PerfusionConfig.set_test_config()
    main()
