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

import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.SensorPoint import SensorPoint
from pyPerfusion.FileStrategy import MultiVarToFile

# TODO: add dict of limits for automation

# Initialize hardware configurations and sensor stream
PerfusionConfig.set_test_config()
roller_pumps = []
sensors = []
rPumpNames = {0: "Dialysate Outflow Pump", 1: "Dialysate Inflow Pump", 2: "Dialysis Blood Pump",
    3: "Glucose Circuit Pump"}

for x in range(4):
    hw = NIDAQDCDevice()
    hw.cfg = pyDC.DCChannelConfig(name=rPumpNames[x])
    hw.read_config()
    sensor = SensorStream(hw, "ml/min")
    sensor.add_strategy(strategy=StreamToFile('Raw', 1, 10))
    roller_pumps.append(hw)
    sensors.append(sensor)

class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, **kwds):
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent

        self._panel_outflow = PanelDC(self, "Dialysate Outflow Pump", roller_pumps[0], sensors[0])
        # wanted to access value --> key in rPumpsNames dict but no joy so manually indexed
        self._panel_glucose = PanelDC(self, "Glucose Circuit Pump", roller_pumps[3], sensors[3])
        self._panel_inflow = PanelDC(self, "Dialysate Inflow Pump", roller_pumps[1], sensors[1])
        self._panel_bloodflow = PanelDC(self, "Dialysis Blood Pump", roller_pumps[2], sensors[2])

        # TODO: add auto_start_btn for dialysis later

        # TODO: add initial rates to config and update this in panel_DC?

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