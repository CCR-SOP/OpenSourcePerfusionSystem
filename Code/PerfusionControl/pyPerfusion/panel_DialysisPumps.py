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
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor
from pyHardware.pyCDI import CDIData
from pyPerfusion.pyAutoDialysis import AutoDialysisInflow, AutoDialysisOutflow


class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, pumps, cdi, auto_inflow, auto_outflow):
        self._lgr = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.pumps = pumps
        self.cdi_sensor = cdi
        self.auto_inflow = auto_inflow
        self.auto_outflow = auto_outflow


        font = wx.Font()
        font.SetPointSize(int(16))

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        static_box.SetFont(font)
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        flagsExpand = wx.SizerFlags(1)
        flagsExpand.Expand().Border(wx.ALL, 10)
        self.sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=1, hgap=1)

        self.panels = []
        for pump in self.pumps:
            pump.start()
            pump.hw.start()
            self.panel = PanelDC(self, pump.name, pump)
            self.sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND, border=1)
            self.panels.append(self.panel)

        # Add auto start button as 5th panel
        self.btn_auto_dialysis = wx.Button(self, label='Start Auto Dialysis')
        self.btn_auto_dialysis.SetFont(font)
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

    def on_auto(self, evt):
        if self.btn_auto_dialysis.GetLabel() == "Start Auto Dialysis":
            self.btn_auto_dialysis.SetLabel("Stop Auto Dialysis")
            self.auto_outflow.start()
            self.auto_inflow.start()
            for panel in self.panels:
                panel.panel_dc.entered_offset.Enable(False)
        else:
            self.btn_auto_dialysis.SetLabel("Start Auto Dialysis")
            self.auto_outflow.stop()
            self.auto_inflow.stop()
            for panel in self.panels:
                panel.panel_dc.entered_offset.Enable(True)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = DialysisPumpPanel(self, pumps, cdi_sensor, auto_inflow, auto_outflow)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.close()
        SYS_HW.stop()
        cdi_sensor.stop()
        for pump in pumps:
            pump.stop()
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

    SYS_HW.load_all()
    SYS_HW.start()

    cdi_sensor = Sensor(name="CDI")
    cdi_sensor.read_config()
    cdi_sensor.start()

    rPumpNames = ['Dialysate Inflow', 'Dialysate Outflow', 'Dialysis Blood', 'Glucose Circuit']
    # Load sensors from pump_names
    pumps = []
    for pump_name in rPumpNames:
        try:
            temp_sensor = Sensor(name=pump_name)
            temp_sensor.read_config()
            pumps.append(temp_sensor)
        except PerfusionConfig.MissingConfigSection:
            print(f'Could not find sensor called {pump_name} in sensors.ini')
            SYS_HW.stop()
            raise SystemExit(1)

    auto_inflow = AutoDialysisInflow(name='Dialysate Inflow Automation')
    auto_inflow.pump = SYS_HW.get_hw('Dialysate Inflow Pump')
    auto_inflow.cdi_reader = cdi_sensor.get_reader()
    auto_inflow.read_config()

    auto_outflow = AutoDialysisOutflow(name='Dialysate Outflow Automation')
    auto_outflow.pump = SYS_HW.get_hw('Dialysate Outflow Pump')
    auto_outflow.cdi_reader = cdi_sensor.get_reader()
    auto_outflow.read_config()

    app = MyTestApp(0)
    app.MainLoop()
