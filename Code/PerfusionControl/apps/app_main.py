# -*- coding: utf-8 -*-
""" Main Liver Perfusion Application

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import threading

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from apps.app_sensors import SensorFrame
from apps.app_hardware_control import HardwareFrame
from pyPerfusion.PerfusionSystem import PerfusionSystem


class MyMainApp(wx.App):
    def OnInit(self):
        frame_hw = HardwareFrame(SYS_PERFUSION, None)
        frame_sensor = SensorFrame(SYS_PERFUSION, None)
        self.SetTopWindow(frame_sensor)
        frame_hw.Show()
        frame_sensor.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.INFO)
    utils.configure_matplotlib_logging()

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

    app = MyMainApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()
