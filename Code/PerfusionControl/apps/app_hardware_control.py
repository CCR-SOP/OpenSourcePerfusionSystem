# -*- coding: utf-8 -*-
""" Application to display all hardware control

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.panel_multiple_syringes import SyringeFrame
from pyPerfusion.panel_DialysisPumps import DialysisPumpPanel
from pyPerfusion.panel_SPCStockertPumps import StockertPumpPanel
from pyPerfusion.panel_PID import PanelPID

# TODO: Insulin, glucagon need the target_vol updated by Dexcom

utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
utils.configure_matplotlib_logging()

# class HardwarePanel(wx.Panel):
    # def __init__(self, parent, **kwds):
      #  wx.Panel.__init__(self, parent, -1)
       # self._lgr = logging.getLogger(__name__)

class HardwareFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)

        self.panel[1] = SyringeFrame()
        self.panel[2] = PanelPID(self)  # needs to be dialysis
        # self.panel[3] = StockertPumpPanel(self)  # needs to be Stockert pumps
        # self.panel[4] =  # needs to be gas mixer thing

        for x in range(4):
            sizer.Add(self.panel[x], 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
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
