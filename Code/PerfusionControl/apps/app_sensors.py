# -*- coding: utf-8 -*-
""" Application to display all sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import threading

import wx

from gui.panel_AI import PanelAI
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem
import pyPerfusion.PerfusionConfig as PerfusionConfig


class SensorPanel(wx.Panel):
    def __init__(self, parent, perfusion_system):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self._lgr = logging.getLogger('SensorPanel')
        self.sys = perfusion_system
        sensor_names = ['Hepatic Artery Flow', 'Portal Vein Flow',
                        'Hepatic Artery Pressure', 'Portal Vein Pressure'
                        ]

        sizer = wx.GridSizer(cols=3)
        self.sensors = {}
        self.panels = []
        for name in sensor_names:
            sensor = self.sys.get_sensor(name)
            self.sensors[name] = sensor
            panel = PanelAI(self, sensor)
            panel.update_frame_ms(30_000)

            self.panels.append(panel)
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.panels:
            panel.Close()
        self.Destroy()


class SensorFrame(wx.Frame):
    def __init__(self, perfusion_system, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

        self.sys = perfusion_system
        self.panel = SensorPanel(self, self.sys)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        if self.panel:
            self.panel.Close()
            self.panel = None
        for child in self.GetChildren():
            child.Close()
        wx.GetApp().close()


class MySensorApp(wx.App):
    def OnInit(self):
        frame = SensorFrame(sys, None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_sensors', logging.DEBUG)
    sys = PerfusionSystem()
    sys.open()
    sys.load_all()

    app = MySensorApp(0)
    app.MainLoop()
    print('MySensorApp closed')
    sys.close()
    for thread in threading.enumerate():
        print(thread.name)


