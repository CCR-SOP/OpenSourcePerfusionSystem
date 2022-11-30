# -*- coding: utf-8 -*-
""" Application to display all hardware control

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.

As of 20221130 - only setup for syringe control
"""
import logging

import wx

from pyPerfusion.panel_AI import PanelAI  # comment out
import pyHardware.pyAI_NIDAQ as NIDAQAI  # comment out
from pyPerfusion.SensorStream import SensorStream  # comment out

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.FileStrategy import StreamToFile
import pyPerfusion.pyPump11Elite as pyPump11Elite

BAUD_RATES = ['9600', '14400', '19200', '38400', '57600', '115200']
drug_dict = {"TPN + Bile Salts": "COM12",
             "Insulin": "COM9",
             "Glucagon": "COM11",
             "Zosyn": "COM10",
             "Phenlyephrine": "COM7",
             "Epoprostenol": "COM8"}

class HardwareFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()

        syringe_total = 6
        self.syringes = []
        for syringe in range (1,syringe_total):
            self.syringes[syringe-1] =


    def OnClose(self, evt):  # UPDATE
        for syringe in self.syringes:
            syringe.stop()
        for panel in self.panel.keys():
            self.panel[panel].Destroy()
        self.Destroy()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    app = MyHardwareApp(0)
    app.MainLoop()