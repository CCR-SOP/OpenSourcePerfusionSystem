# -*- coding: utf-8 -*-
"""Simple test script for testing VCS class
Longer description

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import sleep

from pyHardware.pyVCS import VCS
from pyHardware.pyDIO import DIO
from pyHardware.pyAI_Finite_NIDAQ import AI_Finite_NIDAQ
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.SensorPoint import SensorPoint


logger = logging.getLogger()
utils.setup_stream_logger(logger, logging.DEBUG)


LP_CFG.set_base(basepath='~/Documents/LPTEST')
LP_CFG.update_stream_folder()

dio1 = DIO('valve1')
dio2 = DIO('valve2')
dio3 = DIO('valve3')
dio4 = DIO('valve4')
dio5 = DIO('valve5')
dio1.open('port0', 'line0')
dio2.open('port0', 'line1')
dio3.open('port0', 'line2')
dio4.open('port1', 'line0')
dio5.open('port1', 'line1')


samples = 2
period_ms = 1000
ai = AI_Finite_NIDAQ(period_ms=period_ms, volts_p2p=5, volts_offset=2.5, samples_per_read=samples)
ai.open('Dev4')
ai.add_channel('0')
ai.add_channel('1')
sensor1 = SensorPoint('FiniteAcq1', 'counts', ai)
sensor1.set_ch_id('0')
sensor2 = SensorPoint('FiniteAcq2', 'counts', ai)
sensor2.set_ch_id('1')
sensor1.open(LP_CFG.LP_PATH['stream'])
sensor2.open(LP_CFG.LP_PATH['stream'])
sensor1.start()
sensor2.start()

vcs = VCS(clearance_time_ms=2_000)
vcs.add_cycled_input('chemical', dio1)
vcs.add_cycled_input('chemical', dio2)
vcs.add_cycled_input('chemical', dio3)
vcs.add_independent_input(dio4)
vcs.add_independent_input(dio5)

vcs.add_sensor_to_cycled_valves('chemical', sensor1)
vcs.add_sensor_to_cycled_valves('chemical', sensor2)

logger.info('starting cycle test1')
vcs.start_cycle('chemical')
logger.info('sleeping for 15 seconds')
sleep(15.0)
vcs.open_independent_valve('valve4')
sleep(15.0)
logger.info('closing all valves')
vcs.close_all_valves()
sensor1.stop()
sensor2.stop()
ai.stop()
logger.info('done')
