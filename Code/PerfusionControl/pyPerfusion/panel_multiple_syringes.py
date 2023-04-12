# -*- coding: utf-8 -*-
""" Panel to display multiple (6) syringes together

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.panel_syringe import PanelSyringeControls
from pyPerfusion.Sensor import Sensor
from pyHardware.SystemHardware import SYS_HW


class SyringePanel(wx.Panel):
    def __init__(self, parent, drugs):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.syringes = []
        self.sensors = []

        font_panel_label = wx.Font()
        font_panel_label.SetPointSize(int(12))
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Syringe Infusions")
        static_box.SetFont(font_panel_label)
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        sizer = wx.GridSizer(cols=2)

        self.panel = {}

        for drug in drugs:
            # Initialize sensor
            try:
                sensor = Sensor(name=drug)
                sensor.read_config()
                sensor.start()
                self.sensors.append(sensor)
            except PerfusionConfig.MissingConfigSection:
                print(f'Could not find sensor called {drug} in sensors.ini')
                SYS_HW.stop()
                exit()
                sensor = None

            # Initialize panel
            syringe = sensor.hw
            self.syringes.append(syringe)  # is this redundant?
            self.panel[drug] = PanelSyringeControls(parent=self, syringe=syringe, sensor=sensor)
            self.panel[drug].update_controls_from_config()
            sizer.Add(self.panel[drug], 1, wx.ALL | wx.EXPAND, border=1)


        sizer.SetSizeHints(self.parent)
        self.wrapper.Add(sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.SetSizer(self.wrapper)
        self.Fit()
        self.Layout()

    def OnClose(self, evt):
        for syringe in self.syringes:
            syringe.stop()
        for panel in self.panel.keys():
            self.panel[panel].Destroy()
        for sensor in self.sensors:
            sensor.stop()


class SyringeFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        drugs = ['TPN + Bile Salts', 'Insulin', 'Zosyn', 'Methylprednisone', 'Phenylephrine', 'Epoprostenol']
        self.panel = SyringePanel(self, drugs)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.OnClose(self)
        SYS_HW.stop()
        self.Destroy()


class MySyringeApp(wx.App):
    def OnInit(self):
        frame = SyringeFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_all()

    app = MySyringeApp(0)
    app.MainLoop()
