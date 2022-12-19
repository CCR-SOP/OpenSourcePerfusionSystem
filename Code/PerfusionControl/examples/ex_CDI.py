"""

Example script to parse single set of packet mode data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""

import logging

import pyPerfusion.utils as utils
import pyPerfusion.pyCDI as pyCDI

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)  # add in debugging comments


cdi = pyCDI.CDIStreaming('Test CDI')
cfg = pyCDI.CDIConfig(port='COM13')
cdi.open(cfg)
packet = cdi.request_data()
data = pyCDI.CDIParsedData(packet)
print(f'Arterial pH is {data.arterial_pH}')
print(f'Venous pH is {data.venous_pH}')
print(f'Hemoglobin is {data.hgb}')
