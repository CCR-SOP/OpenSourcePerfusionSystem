# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for general settings for Hepatic Artery branch
"""
import logging
import pyPerfusion.utils as utils

import pyPerfusion.PerfusionConfig as LP_CFG

import wx


class DummyPerfusion:
    ha_min_flow = 0
    ha_max_flow = 100
    ha_rate = 80


class PanelHAParameters(wx.Panel):
    def __init__(self, parent, perfusion):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.perfusion = perfusion
        wx.Panel.__init__(self, parent, -1)

        self.sizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=10)
        self.label_flow = wx.StaticText(self, label='Desired HA Flow\nliters/min')
        self.slider_flow = wx.Slider(self, wx.ID_ANY, value=5, minValue=0, maxValue=10, style=wx.SL_LABELS)

        self.label_rate = wx.StaticText(self, label='Desired HA Rate\nbeats per min')
        self.slider_rate = wx.Slider(self, wx.ID_ANY, value=80, minValue=0, maxValue=200, style=wx.SL_LABELS)

        self.__do_layout()
        # self.__set_bindings()

    def __do_layout(self):
        flags_slider = wx.SizerFlags(1).CenterVertical().Expand()
        flags_label = wx.SizerFlags(0).CenterVertical().Left()

        self.sizer.AddGrowableCol(1, 1)
        self.sizer.Add(self.label_flow, flags_label)
        self.sizer.Add(self.slider_flow, flags_slider)

        self.sizer.Add(self.label_rate, flags_label)
        self.sizer.Add(self.slider_rate, flags_slider)

        self.SetSizer(self.sizer)
        self.Fit()

    # def __set_bindings(self):
        # add bindings, if needed

    def update_gui(self):
        self.slider_flow.SetMin(self.perfusion.ha_min_flow)
        self.slider_flow.SetMax(self.perfusion.ha_max_flow)
        self.slider_rate.SetValue(self.perfusion.ha_rate)

    def update_acq(self):
        self.perfusion.ha_rate = self.slider_rate.GetValue()
        self.perfusion.ha_flow = self.slider_flow.GetValue()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelHAParameters(self, perfusion=DummyPerfusion())


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_default_logging(filename='panel_AO')
    app = MyTestApp(0)
    app.MainLoop()
