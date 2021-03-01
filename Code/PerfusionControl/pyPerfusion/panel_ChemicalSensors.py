# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for plotting output from chemical sensors
"""
import wx

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=3)
        self.acq = NIDAQ_AI(period_ms=1, volts_p2p=5, volts_offset=2.5)
        self._chemical_sensors = [SensorStream('Oxygen', 'mmHg', self.acq),
                                  SensorStream('Carbon Dioxide', 'mmHg', self.acq),
                                  SensorStream('pH', 'Units', self.acq)]
        for sensor in self._chemical_sensors:
            sizer.Add(PanelAI(self, sensor, name=sensor.name), 1, wx.EXPAND, border=2)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self._chemical_sensors:
            sensor.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    app = MyTestApp(0)
    app.MainLoop()
