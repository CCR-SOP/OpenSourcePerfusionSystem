# -*- coding: utf-8 -*-
""" Test script to test functionality of CDI multi-variable reading/saving


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
from pyPerfusion.pyCDI import CDIIndex, CDIData


def main():
    SYS_HW.load_hardware_from_config()
    SYS_HW.start()

    sensor = Sensor(name='CDI')
    sensor.read_config()

    sensor.start()
    reader = sensor.get_reader()
    print('Sleeping for 5 seconds to collect data')
    time.sleep(5)
    cdi_var_index = CDIIndex.arterial_pH.value
    ts, last_samples = reader.retrieve_buffer(5000, 5, index=cdi_var_index)
    print(f'{CDIIndex(cdi_var_index).name}: ts is {ts} and last_samples is {last_samples}')

    print('Sleeping for 5 seconds to collect data')
    time.sleep(5)
    print('Reading full CDI variables, starting from t=0')
    for i in range(3):
        ts, samples = reader.get_data_from_last_read(1)
        print(f'{ts}: sample is {samples}')

    cdi_var_index = CDIIndex.venous_temp.value
    print(f'Getting last acq for {CDIIndex(cdi_var_index).name} index={cdi_var_index}')
    ts, samples = reader.get_last_acq(index=cdi_var_index)
    print(f'{ts}: sample[{cdi_var_index}] is {samples}')
    print(f'{samples}')

    print(f'Convert array of data into a CDIData object')
    ts, all_vars = reader.get_last_acq()
    print(f'{all_vars}')
    cdi_data = CDIData(all_vars)
    try:
        print(f'{CDIIndex(cdi_var_index).name} is {cdi_data.arteriaL_pH}')
    except AttributeError:
        print('arterial_pH is not a valid attribute of CDIData')
    sensor.stop()
    SYS_HW.stop()


if __name__ == '__main__':
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    PerfusionConfig.set_test_config()
    main()
