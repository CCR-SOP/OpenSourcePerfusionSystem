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

samples = 3
filename = LP_CFG.LP_PATH['data'] / '2021-06-24/Oxygen.dat'
logger.info(f'reading from {filename}')
stream_type = np.dtype([('timestamp', np.int32), ('samples', np.float32, samples)])
full_data = np.fromfile(filename, dtype=stream_type)
logger.info(f'total time points: {len(full_data)}')
for ts, data in full_data:
    logger.info(f'Timestamp: {ts/1000.0:.3f}, data: {data}')


