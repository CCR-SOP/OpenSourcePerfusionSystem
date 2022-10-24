"""

Example script to parse single set of packet mode data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""

import logging

import pyPerfusion.utils as utils
import pyPerfusion.pyCDI as pyCDI

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG) # add in debugging comments

COMPORT = 'COM1'

cdi = pyCDI.CDIStreaming('Test CDI')
cdi.open()
packet = cdi.request_data()
data = pyCDI.CDIRawData(packet)
data.print_results()
