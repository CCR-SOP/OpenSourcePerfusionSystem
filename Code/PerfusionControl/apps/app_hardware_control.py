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
from pyPerfusion.panel_SPCStockertPumps import CentrifugalPumpPanel

utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
utils.configure_matplotlib_logging()

class HardwarePanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self._panel_syringes = SyringeFrame(self)
        self._panel_centrifugal_pumps = CentrifugalPumpPanel(self)
        self._panel_dialysate_pumps = DialysisPumpPanel(self)
        # add in gas mixer panel once complete
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Hardware Control App")
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_syringes, flags.Proportion(2))
        self.sizer.Add(self._panel_centrifugal_pumps, flags.Proportion(2))
        self.sizer.Add(self._panel_dialysate_pumps, flags.Proportion(2))

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass

class HardwareFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = HardwarePanel(self)
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
