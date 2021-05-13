# -*- coding: utf-8 -*-
"""Read a data file created by SensorPoint and report basic stats

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import numpy as np

from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG


logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)

LP_CFG.set_base(basepath='~/Documents/LPTEST')
LP_CFG.update_stream_folder()

filename = LP_CFG.LP_PATH['data'] / '2021-05-13/FiniteAcq.dat'
logger.info(f'reading from {filename}')
data = np.fromfile(filename, dtype=np.float32)
logger.info(f'total bytes is {len(data)}')

