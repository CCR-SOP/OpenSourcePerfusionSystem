"""Test program to control GB_100 Gas Mixer based on CDI input

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import threading

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from time import sleep
from pyPerfusion.PerfusionSystem import PerfusionSystem


def main():
    ha_device = SYS_PERFUSION.get_sensor('Arterial Gas Mixer').hw
    pv_device = SYS_PERFUSION.get_sensor('Venous Gas Mixer').hw
    print(f'ha device config is {ha_device.cfg}')

    sample_CDI_output = [1] * 18

    working_status = ha_device.get_working_status()
    print(f'HA device working status is {working_status}')
    working_status = pv_device.get_working_status()
    print(f'PV device working status is {working_status}')

    print('Turn on HA device')
    ha_device.set_working_status(turn_on=True)
    sleep(4)
    working_status = ha_device.get_working_status()
    print(f'HA device working status is {working_status}')

    total_flow = 50
    print(f'Setting HA total flow to {total_flow}')
    ha_device.set_total_flow(total_flow)

    percent = 10
    print(f'Setting HA second channel to {percent}')
    ha_device.set_percent_value(2, percent)

    sleep(2)
    ha_device.set_working_status(turn_on=True)
    sleep(2)

    print('Turn off HA device')
    ha_device.set_working_status(turn_on=False)
    working_status = ha_device.get_working_status()
    print(f'HA device working status is {working_status}')


if __name__ == '__main__':
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, 'ex_GB100')

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
