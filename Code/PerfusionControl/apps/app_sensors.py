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

from pyPerfusion.panel_AI import PanelAI
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem


class SensorFrame(wx.Frame):
    def __init__(self, perfusion_system, *args, **kwds):
        self._lgr = logging.getLogger('AppSensors')
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()

        self.sys = perfusion_system
        sensor_names = ['Hepatic Artery Flow', 'Portal Vein Flow', 'Hepatic Artery Pressure', 'Portal Vein Pressure']
        self.sensors = {}
        self.panels = []
        for name in sensor_names:
            sensor = self.sys.get_sensor(name)
            self.sensors[name] = sensor
            if name == "Hepatic Artery Flow":
                panel = PanelAI(self, sensor, reader=sensor.get_reader('MovAvg_11pt'))
            else:
                panel = PanelAI(self, sensor, reader=sensor.get_reader())
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


class MySensorApp(wx.App):
    def OnInit(self):
        frame = SensorFrame(sys, None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    sys = PerfusionSystem()
    sys.load_all()
    sys.open()

    app = MySensorApp(0)
    app.MainLoop()
    for thread in threading.enumerate():
        print(thread.name)

    sys.close()
