# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for initiating syringe injections based on pressure/flow conditions
"""
import wx

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG

class PanelTestPressure(wx.Panel):
    def __init__(self, parent, sensor, name, dev, line):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._dev = dev
        self._line = line
        self._ao = NIDAQ_AO()
        self._inc = 0.025

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.label_desired_output = wx.StaticText(self, label='Desired ' + self._name)
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=100, initial=50, inc=self._inc)

        self.label_tolerance = wx.StaticText(self, label='Tolerance (mmHg)')
        self.spin_tolerance = wx.SpinCtrl(self, min=0, max=100, initial=10)

        self.label_increment = wx.StaticText(self, label='Voltage Increment')
        self.spin_increment = wx.SpinCtrlDouble(self, min=0, max=1, initial=0, inc=0.01)

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

        self.timer_pressure_adjust = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_label.Add(self.label_desired_output, flags)
        self.sizer_label.Add(self.spin_desired_output, flags)

        self.sizer_tol = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_tol.Add(self.label_tolerance, flags)
        self.sizer_tol.Add(self.spin_tolerance, flags)

        self.sizer_increment = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_increment.Add(self.label_increment, flags)
        self.sizer_increment.Add(self.spin_increment, flags)

        sizer = wx.GridSizer(cols=1)
        sizer.Add(self.sizer_label)
        sizer.Add(self.sizer_tol)
        sizer.Add(self.sizer_increment, flags)
        sizer.Add(self.btn_stop, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)

    def OnStartStop(self, evt):
        state = self.btn_stop.GetLabel()
        if state == 'Start':
            self._ao.open(period_ms=100, dev=self._dev, line=self._line)
            self._ao.set_dc(0)
            self.timer_pressure_adjust.Start(1000, wx.TIMER_CONTINUOUS)
        else:
            self.timer_pressure_adjust.Stop()
            self._ao.close()
            self._ao.halt()

    def OnTimer(self, event):
        if event.GetId() == self.timer_pressure_adjust.GetId():
            self.update_output()

    def update_output(self):
        pressure = float(self._sensor.get_current())
        desired = float(self.spin_desired_output.GetValue())
        tol = float(self.spin_tolerance.GetValue())
        inc = float(self.spin_increment.GetValue())
        dev = abs(desired - pressure)
        print(f'Pressure is {pressure:.3f}, desired is {desired:.3f}')
        print(f'Deviation is {dev}, tol is {tol}')
        if dev > tol:
            if pressure < desired:
                new_val = self._ao._volts_offset + inc
            else:
                new_val = self._ao._volts_offset - inc
            self._ao.set_dc(new_val)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        self.acq =  NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.pressure_sensors = {
            SensorStream('Hepatic Artery Pressure', 'mmHg', self.acq): ['Dev3', 1],
            SensorStream('Portal Vein Pressure', 'mmHg', self.acq): ['Dev3', 0]
        }

        for sensor, pump in self.pressure_sensors.items():
            sizer.Add(PanelAI(self, sensor, name=sensor.name), 1, wx.ALL | wx.EXPAND, border=1)
            sizer.Add(PanelTestPressure(self, sensor, name=sensor.name, dev=pump[0], line=pump[1]), 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self.pressure_sensors.keys():
            sensor.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    app = MyTestApp(0)
    app.MainLoop()
