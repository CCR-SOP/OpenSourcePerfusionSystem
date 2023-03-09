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
from pyPerfusion.panel_DC import PanelDC
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
import pyHardware.pyDC as pyDC
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.SensorStream import SensorStream


class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, **kwds):
        self._lgr = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        self.parent = parent

        # Initialize hardware configurations and sensor stream
        self.roller_pumps = {}
        self.rPumpNames = ["Dialysate Outflow Pump", "Dialysate Inflow Pump",
                           "Dialysis Blood Pump", "Glucose Circuit Pump"]

        for pumpName in self.rPumpNames:
            hw = NIDAQDCDevice()
            hw.cfg = pyDC.DCChannelConfig(name=pumpName)
            hw.read_config()
            sensor = SensorStream(hw, "ml/min")
            sensor.add_strategy(strategy=StreamToFile('Raw', 1, 10))
            self.roller_pumps[pumpName] = sensor

        self._panel_outflow = PanelDC(self, self.roller_pumps['Dialysate Outflow Pump'])
        self._panel_glucose = PanelDC(self, self.roller_pumps['Glucose Circuit Pump'])
        self._panel_inflow = PanelDC(self, self.roller_pumps['Dialysate Inflow Pump'])
        self._panel_bloodflow = PanelDC(self, self.roller_pumps['Dialysis Blood Pump'])

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.automatic_start_btn = wx.ToggleButton(self, label='Start Automatic')

        self.cdi_timer = wx.Timer(self)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self._panel_outflow.close()
        self._panel_inflow.close()
        self._panel_glucose.close()
        self._panel_bloodflow.close()

    def __do_layout(self):
        flagsExpand = wx.SizerFlags(1)
        flagsExpand.Expand().Border(wx.ALL, 10)
        self.sizer = wx.GridSizer(cols=2)

        self.sizer.Add(self._panel_inflow, flagsExpand)
        self.sizer.Add(self._panel_outflow, flagsExpand)
        self.sizer.Add(self._panel_bloodflow, flagsExpand)
        self.sizer.Add(self._panel_glucose, flagsExpand)
        self.sizer.Add(self.automatic_start_btn, flagsExpand)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.automatic_start_btn.Bind(wx.EVT_TOGGLEBUTTON, self.OnAutoStart)

    def OnAutoStart(self, evt):
        if self.automatic_start_btn.GetLabel() == "Start Automatic":
            self.automatic_start_btn.SetLabel('Stop Automatic')
            self.cdi_timer.Start(300_000, wx.TIMER_CONTINUOUS)
        else:
            self.automatic_start_btn.SetLabel('Stop Automatic')
            self.cdi_timer.Stop()

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
    logger = logging.getLogger()
    utils.setup_stream_logger(logger, logging.DEBUG)
    utils.configure_matplotlib_logging()

    app = MyTestApp(0)
    app.MainLoop()
