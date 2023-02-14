# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from threading import enumerate
from time import sleep
import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.panel_AO import PanelDC
# from pyHardware.pyAO_NIDAQ import NIDAQAODevice
import pyHardware.pyAO as pyAO
import pyHardware.pyDC as pyDC
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
from pyPerfusion.FileStrategy import StreamToFile

import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.SensorPoint import SensorPoint
from pyPerfusion.FileStrategy import MultiVarToFile

# TODO: add dict of limits

class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, **kwds):
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent

        self._panel_outflow = PanelDC(self, "Dialysate Outflow Pump")
        self._panel_glucose = PanelDC(self, "Glucose Circuit Pump")
        self._panel_inflow = PanelDC(self, "Dialysate Inflow Pump")
        self._panel_bloodflow = PanelDC(self, "Dialysis Blood Pump")

        # TODO: add auto_start_btn for dialysis later

        # TODO: add initial rates to config and update this in panel_AO?

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self._panel_outflow.close()
        self._panel_inflow.close()
        self._panel_glucose.close()
        self._panel_bloodflow.close()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        self.sizer = wx.GridSizer(cols=2)

        self.sizer.Add(self._panel_inflow, flags.Proportion(2))
        self.sizer.Add(self._panel_outflow, flags.Proportion(2))
        self.sizer.Add(self._panel_bloodflow, flags.Proportion(2))
        self.sizer.Add(self._panel_glucose, flags.Proportion(2))

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass

    # def OnStartAuto(self, evt):
        # label = self.auto_start_btn.GetLabel()
        # if label == "Start Automatic":
            # self.auto_start_btn.SetLabel('Stop Automatic')
            # turn things on - Allen's OnDIalysis
            # self.AutomaticDialysis()
        # elif label == "Stop Automatic":
            # self.auto_start_btn.SetLabel('Start Automatic')
            # turn things off - Allen's OnDialysis
        # check limits of dialysis and that difference isn't too high- see dict - make sure all are true
        # accept values from CDI - see panel_gas_mixers for example (but check with John before you do it)
        # if K and hct are in range, don't run dialysis
        # if either is out of range,  gentle dialysis
        # be able to flip whether inflow or outflow is higher if trend gets reversed
        # necessary hardware functioning to read everything in

    # def AutomaticDialysis(self):
        # time.sleep(5.0)
        # pick initial rates for auto - 3 mL/min in and out? may end up changing this
        # add functionality - UpdateDialysis methods

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = DialysisPumpPanel(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.Destroy()
        self.panel.close()

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