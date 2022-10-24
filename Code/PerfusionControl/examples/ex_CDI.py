"""

Example script to parse single set of packet mode data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""

import logging

import pyPerfusion.utils as utils
import pyPerfusion.pyCDI as pyCDI

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG) # add in debugging comments

COMPORT = 'COM13'

cdi = pyCDI.CDIStreaming('Test CDI')
cdi.open(COMPORT, 9600)
packet = cdi.request_data()
cdi.print_raw_results(packet)
data = pyCDI.CDIRawData(packet)
data.print_results()
