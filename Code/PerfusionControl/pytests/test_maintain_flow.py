# -*- coding: utf-8 -*-
"""Provides test app for controlling a flow based on a PID

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import wx

from simple_pid import PID

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_PID import PanelPID

class PanelTestMaintainFlow(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        self._inc = 0.1

        self.pid = PID(1.0, 0.1, 0.05, setpoint=1)
        self.pid.sample_time = 0.001
        self._ai = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self._ao = NIDAQ_AO()
        self._ao.open(line=1, period_ms=100, dev='Dev3')
        self._ai.add_channel(channel_id=3)
        self._ai.open(dev='Dev1')
        self._sensor = SensorStream('Flow sensor', 'ml/min', self._ai)

        self.panel_pid = PanelPID(self)
        self.panel_pid.set_pid(self.pid)

        self.label_ai = wx.StaticText(self, label=f'Using Analog Input Dev1/ai3')
        self.label_ao = wx.StaticText(self, label=f'Using Analog Output Dev3/ao1')
        self.label_output = wx.StaticText(self, label='Analog Output is xxx')

        self.label_desired_output = wx.StaticText(self, label='Desired Output')
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=1.0, initial=0.5, inc=self._inc)
        self.spin_desired_output.Digits = 3

        self.panel_plot = PanelPlotting(self)
        LP_CFG.update_stream_folder()
        self._sensor.open(LP_CFG.LP_PATH['stream'])
        self._ao.set_dc(0)

        self.panel_plot.add_sensor(self._sensor)
        self._sensor.start()

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

        self.timer_flow_adjust = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_ai)
        sizer.Add(self.label_ao)
        self.sizer.Add(sizer, flags)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_desired_output, flags)
        sizer.Add(self.spin_desired_output, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.panel_pid, flags)
        sizer.Add(self.btn_stop, flags)
        self.sizer.Add(sizer)

        self.sizer.Add(self.label_output, flags)

        self.sizer.AddSpacer(20)
        self.sizer.Add(self.panel_plot, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)

    def OnStartStop(self, evt):
        if self.btn_stop.GetValue():
            self._sensor.set_ch_id(3)
            self._sensor.hw.start()
            self._ao.start()
            self.btn_stop.SetLabel('Stop')
            self.update_output()
            self.timer_flow_adjust.Start(1000, wx.TIMER_CONTINUOUS)
        else:
            self._ao.halt()
            self._sensor.stop()
            self.btn_stop.SetLabel('Start')
            self.timer_flow_adjust.Stop()

    def OnTimer(self, event):
        if event.GetId() == self.timer_flow_adjust.GetId():
            self.update_output()

    def update_output(self):
        flow = self._sensor.get_current()
        self.pid.setpoint = self.spin_desired_output.GetValue()
        new_val = self.pid(flow)
        self._ao.set_dc(new_val)
        self.label_output.SetLabel(f'Analog output is {new_val:.3f}')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.ao = NIDAQ_AO()
        ao_name = 'Analog Output'
        self.panel = PanelTestMaintainFlow(self)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
