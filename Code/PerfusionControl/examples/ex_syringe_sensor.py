# -*- coding: utf-8 -*-
""" Simple test program for demonstrating basic use of  a syringe and saving
    action data

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import threading
import time

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem


def main():
    name = 'Phenylephrine'
    sensor = SYS_PERFUSION.get_sensor(name)

    reader = sensor.get_reader()
    syringe = sensor.hw
    #
    print('setting target volume')
    syringe.set_target_volume(volume_ul=10_000)
    syringe.set_infusion_rate(rate_ul_min=1_000)
    syringe.infuse_to_target_volume()
    time.sleep(2.0)
    syringe.set_target_volume(volume_ul=3_000)
    syringe.set_infusion_rate(rate_ul_min=5_000)
    syringe.infuse_to_target_volume()

    # call APIs to record responses in log
    syringe.clear_infusion_volume()
    syringe.get_infusion_rate()
    syringe.get_target_volume()
    syringe.clear_target_volume()
    syringe.get_infused_volume()
    syringe.clear_syringe()

    #
    syringe.close()
    logging.getLogger().info('******END OF EXAMPLE')
    #
    # time.sleep(1.0)
    # ts, last_samples = reader.retrieve_buffer(5000, 5)
    # for ts, samples in zip(ts, last_samples):
    #     print(f'{ts}: sample is {samples}')


if __name__ == '__main__':
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, 'ex_syringe_sensor')

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
