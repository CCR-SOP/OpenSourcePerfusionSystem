# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import time
from pyPerfusion.panel_AO import PanelAODCControl
from pyPerfusion.pyDialysatePumps import DialysatePumps

import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.SensorPoint import SensorPoint
# from pyPerfusion.FileStrategy import MultiVarToFile  # not in this branch

# add dict of limits

class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, **kwds):  # add pump as an argument - just skeletonized right now
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent
        # self.pump = pump

        static_box = wx.StaticBox(self, wx.ID_ANY, label='Dialysis Pumps')
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_inflow = wx.StaticText(self, label='Dialysate inflow pump flow rate (mL/min):')
        self.input_inflow_rate = wx.TextCtrl(self, wx.ID_ANY, value='5')

        self.label_outflow = wx.StaticText(self, label='Dialysate outflow pump flow rate (mL/min):')
        self.input_outflow_rate = wx.TextCtrl(self, wx.ID_ANY, value='5')

        self.start_btn_inflow = wx.ToggleButton(self, label='Start Manual')
        self.start_btn_outflow = wx.ToggleButton(self, label='Start Manual')
        self.auto_start_btn = wx.ToggleButton(self, label='Start Automatic')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        sizer_cfg = wx.GridSizer(cols=3)

        sizer_cfg.Add(self.label_inflow, flags)
        sizer_cfg.Add(self.input_inflow_rate, flags)
        sizer_cfg.Add(self.start_btn_inflow, flags)

        sizer_cfg.Add(self.label_outflow, flags)
        sizer_cfg.Add(self.input_outflow_rate, flags)
        sizer_cfg.Add(self.start_btn_outflow, flags)

        sizer_cfg.Add(self.auto_start_btn, flags)

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.start_btn_inflow.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartInflow)
        self.start_btn_outflow.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartOutflow)
        self.auto_start_btn.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartAuto)
        # do we need something to accept the text input?

    def OnStartInflow(self, evt):
        # write something to open
        label = self.start_btn_inflow.GetLabel()
        if label == "Start Manual":
            self.start_btn_inflow.SetLabel('Stop Manual')
        elif label == "Stop Manual":
            self.start_btn_inflow.SetLabel('Start Manual')

    def OnStartOutflow(self, evt):
        # write something to open
        label = self.start_btn_outflow.GetLabel()
        if label == "Start Manual":
            self.start_btn_outflow.SetLabel('Stop Manual')
        elif label == "Stop Manual":
            self.start_btn_outflow.SetLabel('Start Manual')

    def OnStartAuto(self, evt):
        label = self.auto_start_btn.GetLabel()
        if label == "Start Automatic":
            self.auto_start_btn.SetLabel('Stop Automatic')
            # turn things on - Allen's OnDIalysis
            self.AutomaticDialysis()
        elif label == "Stop Automatic":
            self.auto_start_btn.SetLabel('Start Automatic')
            # turn things off - Allen's OnDialysis
        # check limits of dialysis and that difference isn't too high- see dict - make sure all are true
        # accept values from CDI - see panel_gas_mixers for example (but check with John before you do it)
        # if K and hct are in range, don't run dialysis
        # if either is out of range,  gentle dialysis
        # be able to flip whether inflow or outflow is higher if trend gets reversed
        # necessary hardware functioning to read everything in

    def AutomaticDialysis(self):
        time.sleep(5.0)
        # pick initial rates for auto - 3 mL/min in and out? may end up changing this
        # add functionality - UpdateDialysis methods

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        # self.pump = DialysatePumps('Mock Pump')

        self.panel = DialysisPumpPanel(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        # self.pump.close()  # need method for this
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()