# -*- coding: utf-8 -*-
""" Main Liver Perfusion Application

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from apps.app_sensors import SensorFrame
from apps.app_hardware_control import HardwareFrame
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor


class MyMainApp(wx.App):
    def OnInit(self):
        frame_hw = HardwareFrame(None, wx.ID_ANY, "")
        frame_sensor = SensorFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame_hw)
        frame_hw.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()
    SYS_HW.start()
    rPumpNames = ['Dialysate Inflow', 'Dialysate Outflow', 'Dialysis Blood', 'Glucose Circuit']

    # Load CDI sensor
    cdi_sensor = Sensor(name='CDI')
    cdi_sensor.read_config()

    app = MyMainApp(0)
    app.MainLoop()
