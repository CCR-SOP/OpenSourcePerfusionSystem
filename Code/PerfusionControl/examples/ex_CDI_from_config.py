"""

Example script to show how to open a CDI object from the config file

Assumes the current test_config has an appropriate configuration called Test CDI

@project: Liver Perfusion, NIH
@author: John Kakareka, NIH

"""

import logging

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyCDI as pyCDI

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)  # add in debugging comments

cdi = pyCDI.CDIStreaming('Test CDI')
cdi.read_config()
print(f'Read config for {cdi.name}: ComPort={cdi.cfg.port}, ',
      f'Sampling Period (ms)={cdi.cfg.sampling_period_ms}, ',
      f'Samples per read (ms) = {cdi.cfg.samples_per_read}')
print('Attempting to read data')
packet = cdi.request_data()
data = pyCDI.CDIParsedData(packet)
data.print_results()
