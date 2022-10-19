# -*- coding: utf-8 -*-
""" Simple example to show how to read syringe info from config

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.pyPump11Elite as pyPump11Elite
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig

PerfusionConfig.set_test_config()


logger = logging.getLogger()

utils.setup_stream_logger(logger, logging.DEBUG)
syringe = pyPump11Elite.MockPump11Elite(name='Example')
syringe.read_config()

syringe.set_target_volume(volume_ul=10_000)
syringe.set_infusion_rate(rate_ul_min=1_000)
syringe.infuse_to_target_volume()
syringe.close()
