# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for general settings for Portal Vein branch parameters
"""
import logging

import wx

import pyPerfusion.utils as utils
from pyPerfusion.PerfusionConfig import LP_CFG



class DummyPerfusion:
    pv_desired_flow = 5000


class PanelPVParameters(wx.Panel):
    def __init__(self, parent, perfusion):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.perfusion = perfusion
        wx.Panel.__init__(self, parent, -1)

        self.sizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=10)
        self.label_flow = wx.StaticText(self, label='Desired HA Flow\nmilliliters/min')
        self.slider_flow = wx.Slider(self, wx.ID_ANY, value=500, minValue=0, maxValue=5000, style=wx.SL_LABELS)

        self.__do_layout()
        # self.__set_bindings()

    def __do_layout(self):
        flags_slider = wx.SizerFlags(1).CenterVertical().Expand()
        flags_label = wx.SizerFlags(0).CenterVertical().Left()

        self.sizer.AddGrowableCol(1, 1)
        self.sizer.Add(self.label_flow, flags_label)
        self.sizer.Add(self.slider_flow, flags_slider)

        self.SetSizer(self.sizer)
        self.Fit()

    # def __set_bindings(self):
        # add bindings, if needed

    def update_gui(self):
        self.slider_flow.SetMin(self.perfusion.pv_desired_flow)

    def update_acq(self):
        self.perfusion.pv_desired_flow = self.slider_flow.GetValue()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPVParameters(self, perfusion=DummyPerfusion())


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_default_logging(filename='panel_pv_parameters')
    app = MyTestApp(0)
    app.MainLoop()
