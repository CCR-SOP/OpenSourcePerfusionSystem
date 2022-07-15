"""
@author: Stephie Lux
Panel to introduce temperature graph

Immediate needs: figure out input information for temperature sensor, run test_plot_stream, decide on processing strategy for temperature
"""

import wx
import time
import logging

from pyPerfusion.plotting import SensorPlot, PanelPlotting
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy
import pyPerfusion.utils as utils

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()