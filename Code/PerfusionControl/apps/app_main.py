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
        frame_sensor = SensorFrame(sys, None, wx.ID_ANY, "")
        frame_hw = HardwareFrame(sys, frame_sensor, wx.ID_ANY, "")

        self.SetTopWindow(frame_sensor)

        frame_hw.Show()
        frame_sensor.Show()
        return True

    def close(self):
        sys.close()


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_main', logging.DEBUG)
    sys = PerfusionSystem()
    sys.open()
    sys.load_all()
    sys.load_automations()

    app = MyMainApp(0)
    app.MainLoop()
    print('MyMain app closed')
    sys.close()
    for thread in threading.enumerate():
        print(thread.name)
