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
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile


class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, roller_pumps, cdi_data, **kwds):
        self._lgr = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        self.parent = parent
        self.cdi_data = cdi_data
        self.roller_pumps = roller_pumps

        self._panel_outflow = PanelDC(self, self.roller_pumps['Dialysate Outflow Pump'])
        self._panel_glucose = PanelDC(self, self.roller_pumps['Glucose Circuit Pump'])
        self._panel_inflow = PanelDC(self, self.roller_pumps['Dialysate Inflow Pump'])
        self._panel_bloodflow = PanelDC(self, self.roller_pumps['Dialysis Blood Pump'], self.cdi_data)

        # Add auto start button as 5th panel
        font_btn = wx.Font()
        font_btn.SetPointSize(int(16))
        self.btn_auto_dialysis = wx.Button(self, label='Start Auto Dialysis')
        self.btn_auto_dialysis.SetFont(font_btn)
        self.cdi_timer = wx.Timer(self)

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        static_box.SetFont(font_btn)
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

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
        self.sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=1, hgap=1)

        self.sizer.Add(self._panel_inflow, flagsExpand)
        self.sizer.Add(self._panel_outflow, flagsExpand)
        self.sizer.Add(self._panel_bloodflow, flagsExpand)
        self.sizer.Add(self._panel_glucose, flagsExpand)
        self.sizer.Add(self.btn_auto_dialysis, flagsExpand)

        self.sizer.AddGrowableRow(0, 3)
        self.sizer.AddGrowableRow(1, 3)
        self.sizer.AddGrowableRow(2, 1)

        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.SetSizer(self.wrapper)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_auto_dialysis.Bind(wx.EVT_BUTTON, self.on_auto)

    def on_auto(self, evt):
        if self.btn_auto_dialysis.GetLabel() == "Start Auto Dialysis":
            self.btn_auto_dialysis.SetLabel("Stop Auto Dialysis")
            self.cdi_timer.Start(60_000, wx.TIMER_CONTINUOUS)  # TODO: update to 5 or 10 minutes
        else:
            self.btn_auto_dialysis.SetLabel("Start Auto Dialysis")
            self.cdi_timer.Stop()

    def pullDataFromCDI(self, evt):
        if self.cdi_data is None:
            self._lgr.debug(f'No CDI data. Cannot run automatically')
        else:
            if evt.GetId() == self.cdi_timer.GetId():
                packet = self.cdi_data.request_data()
                data = pyCDI.CDIParsedData(packet)
                # data = self.cdi_data.retrieve_buffer()  # assume this works
                self.update_dialysis(data)

    def update_dialysis(self, cdi_input):
        # TODO: Add ceilings and error cases
        if cdi_input.hgb < 7:
            self._lgr.debug('Hemoglobin is low. Increasing dialysate outflow')
            # current_flow_rate = 10  # TODO: GET CURRENT FLOW RATE
            # new_flow_rate = current_flow_rate + 1
            # self._panel_outflow.sensor.hw.set_output(int(new_flow_rate))
        elif cdi_input.hgb > 12:
            self._lgr.debug(f'Hemoglobin is high. Increasing dialysate inflow')
            # current_flow_rate = something
            # new_flow_rate = current_flow_rate + 1
            # self._panel_inflow.sensor.hw.set_output(int(new_flow_rate))
        elif cdi_input.K > 6:
            self._lgr.debug(f'K is high. Increasing rates of dialysis')
            # current_flow_rate = something
            # new_flow_rate = current_flow_rate + 1
            # self._panel_inflow.sensor.hw.set_output(int(new_flow_rate))
        else:
            self._lgr.debug(f'Dialysis can continue at a stable rate')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = DialysisPumpPanel(self, roller_pumps=r_pumps, cdi_data=cdi_object)
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

    # Initialize pumps
    r_pumps = {}
    rPumpNames = ["Dialysate Outflow Pump", "Dialysate Inflow Pump",
                       "Dialysis Blood Pump", "Glucose Circuit Pump"]
    for pumpName in rPumpNames:
        hw = NIDAQDCDevice()
        hw.cfg = pyDC.DCChannelConfig(name=pumpName)
        hw.read_config()
        sensor = SensorStream(hw, "ml/min")
        sensor.add_strategy(strategy=StreamToFile('Raw', 1, 10))
        r_pumps[pumpName] = sensor

    # Initialize CDI
    cdi_object = pyCDI.CDIStreaming('CDI')
    cdi_object.read_config()
    stream_cdi_to_file = SensorPoint(cdi_object, 'NA')
    stream_cdi_to_file.add_strategy(strategy=MultiVarToFile('write', 1, 17))
    ro_sensor = ReadOnlySensorPoint(cdi_object, 'na')
    read_from_cdi = MultiVarFromFile('multi_var', 1, 17, 1)
    ro_sensor.add_strategy(strategy=read_from_cdi)
    stream_cdi_to_file.start()
    cdi_object.start()

    app = MyTestApp(0)
    app.MainLoop()
