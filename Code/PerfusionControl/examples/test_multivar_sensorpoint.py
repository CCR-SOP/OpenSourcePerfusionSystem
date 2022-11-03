# -*- coding: utf-8 -*-
""" Test script to test functionality of multi-variable reading/saving


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import serial
import time

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint

COMPORT = 'COM13'


def main():
    fake_port = serial.serial_for_url('loop://')
    cdi = pyCDI.CDIStreaming('Test CDI')
    cdi.open(fake_port, 9600)

    sensorpt = SensorPoint('multi_var', 'na', cdi)
    write_strategy = MultiVarToFile('write', 1, 17)
    write_strategy.open(PerfusionConfig.get_date_folder(), f'{sensorpt.name}_raw', sensorpt.params)
    sensorpt.add_strategy(write_strategy)
    sensorpt.set_ch_id(0)

    ro_sensorpt = ReadOnlySensorPoint('multi_var', 'na', cdi)

    read_strategy = MultiVarFromFile('multi_var', 1, 17, 1)
    read_strategy.open(PerfusionConfig.get_date_folder(), f'{sensorpt.name}_raw', ro_sensorpt.params)
    ro_sensorpt.add_strategy(read_strategy)

    sensorpt.start()
    # ro_sensorpt.start()
    cdi.start()

    data = list(range(17))
    for i in range(5):
        cdi_str = 'abc\t' + '\t'.join(f'{d:02x}{d+i:04d}' for d in data)
        print(f'writing {cdi_str}')
        fake_port.write(bytes(cdi_str + '\n', 'ascii'))
        time.sleep(1)
        # print(cdi.request_data(timeout=1))
        #print(f'Last acq is : {read_strategy.get_last_acq()}')
    # print(f'Last 5 samples are {read_strategy.get_data_from_last_read(timestamp=0)}')
    print(f'Last 5 samples are {read_strategy.retrieve_buffer(last_ms=-1, samples_needed=5)}')

    cdi.stop()
    sensorpt.stop()
    ro_sensorpt.stop()

if __name__ == '__main__':
    # utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    PerfusionConfig.set_test_config()
    main()
