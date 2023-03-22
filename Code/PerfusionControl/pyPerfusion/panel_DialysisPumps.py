# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import wx
from time import sleep

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.panel_DC import PanelDC
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor

class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, pump_sensors, **kwds):
        self._lgr = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        self.parent = parent
        self.sensors = pump_sensors

        font = wx.Font()
        font.SetPointSize(int(16))

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        static_box.SetFont(font)
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        flagsExpand = wx.SizerFlags(1)
        flagsExpand.Expand().Border(wx.ALL, 10)
        self.sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=1, hgap=1)

        self.panels = []

        for sensor in self.sensors:
            sensor.start()
            sensor.hw.start()
            self.panel = PanelDC(self, sensor.name, sensor)
            self.sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND, border=1)
            self.panels.append(self.panel)

        # Add auto start button as 5th panel
        self.btn_auto_dialysis = wx.Button(self, label='Start Auto Dialysis')
        self.btn_auto_dialysis.SetFont(font)
        self.cdi_timer = wx.Timer(self)
        self.sizer.Add(self.btn_auto_dialysis, flagsExpand)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        for panel in self.panels:
            panel.close()

    def __do_layout(self):
        self.sizer.AddGrowableRow(0, 3)
        self.sizer.AddGrowableRow(1, 3)
        self.sizer.AddGrowableRow(2, 1)
        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableCol(1, 1)

        self.sizer.SetSizeHints(self.parent)
        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.SetSizer(self.wrapper)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        self.btn_auto_dialysis.Bind(wx.EVT_BUTTON, self.on_auto)
        self.Bind(wx.EVT_TIMER, self.pullDataFromCDI, self.cdi_timer)

    def on_auto(self, evt):
        if self.btn_auto_dialysis.GetLabel() == "Start Auto Dialysis":
            self.btn_auto_dialysis.SetLabel("Stop Auto Dialysis")
            self.cdi_timer.Start(300_000, wx.TIMER_CONTINUOUS)
        else:
            self.btn_auto_dialysis.SetLabel("Start Auto Dialysis")
            self.cdi_timer.Stop()

    def pullDataFromCDI(self, evt):
        if evt.GetId() == self.cdi_timer.GetId():
            if self.cdi_data is not None:
                # TODO: add stuff from ex_CDI_sensor
                self.update_dialysis(data)  # says this is missing attributes but it's not
            else:
                self._lgr.debug(f'No CDI data. Cannot run dialysis automatically')

    def update_dialysis(self, cdi_input):
        # TODO: Add ceilings and error cases
        if cdi_input.hgb == -1:
            self._lgr.warning(f'Hemoglobin is out of range. Cannot be adjusted automatically')
        elif 0 < cdi_input.hgb < 7:
            self._lgr.debug(f'Hemoglobin is low at {cdi_input.hgb}. Increasing dialysate outflow')
            # current_flow_rate = 10  # TODO: GET CURRENT FLOW RATE
            # new_flow_rate = current_flow_rate + 1
            # self._panel_outflow.sensor.hw.set_output(int(new_flow_rate))
        elif cdi_input.hgb > 12:
            self._lgr.debug(f'Hemoglobin is high at {cdi_input.hgb}. Increasing dialysate inflow')
            # current_flow_rate = something
            # new_flow_rate = current_flow_rate + 1
            # self._panel_inflow.sensor.hw.set_output(int(new_flow_rate))
        else:
            self._lgr.debug(f'No need to increase or decrease relative inflow/outflow rates')

        if cdi_input.K == -1:
            self._lgr.warning(f'K is out of range. Cannot be adjusted automatically')
        elif 0 < cdi_input.K > 6:
            self._lgr.debug(f'K is high at {cdi_input.K}. Increasing rates of dialysis')
            # current_inflow_rate = something
            # new_inflow_rate = current_flow_rate + 1
            # self._panel_inflow.sensor.hw.set_output(int(new_inflow_rate))
            # current_outflow_rate = something
            # new_outflow_rate = current_flow_rate + 1
            # self._panel_outflow.sensor.hw.set_output(int(new_outflow_rate))
        elif cdi_input.K < 2:
            self._lgr.debug(f'K is stable {cdi_input.K}. Decreasing rates of dialysis')
            # current_inflow_rate = something
            # new_inflow_rate = current_flow_rate - 1
            # self._panel_inflow.sensor.hw.set_output(int(new_inflow_rate))
            # current_outflow_rate = something
            # new_outflow_rate = current_flow_rate - 1
            # self._panel_outflow.sensor.hw.set_output(int(new_outflow_rate))
        else:
            self._lgr.debug(f'Dialysis can continue at a stable rate')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = DialysisPumpPanel(self, sensors)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.close()
        SYS_HW.stop()
        self.panel.cdi_timer.Stop()
        for sensor in self.panel.sensors:
            sensor.stop()
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

    SYS_HW.load_hardware_from_config()

    rPumpNames = ['Dialysate Inflow', 'Dialysate Outflow', 'Dialysis Blood', 'Glucose Circuit']
    sensors = []
    for pump_name in rPumpNames:
        try:
            temp_sensor = Sensor(name=pump_name)
            temp_sensor.read_config()
            sensors.append(temp_sensor)
        except PerfusionConfig.MissingConfigSection:
            print(f'Could not find sensor called {pump_name} in sensors.ini')
            SYS_HW.stop()
            raise SystemExit(1)

    app = MyTestApp(0)
    app.MainLoop()
