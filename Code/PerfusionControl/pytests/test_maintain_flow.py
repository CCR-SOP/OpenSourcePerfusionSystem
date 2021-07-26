# -*- coding: utf-8 -*-
"""Provides test app for controlling a flow based on a PID

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import wx

from simple_pid import PID

from pyHardware.pyAI import AIDeviceException
from pyHardware.pyAO import AODeviceException
from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.plotting import PanelPlotting, SensorPlot
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_PID import PanelPID
from pyPerfusion.FileStrategy import StreamToFile

class PanelTestMaintainFlow(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        self._inc = 0.1

        self.pid = PID(1.0, 0.1, 0.05, setpoint=1)
        self.pid.sample_time = 0.001
        self.panel_pid = PanelPID(self)
        self.panel_pid.set_pid(self.pid)

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()

        try:
            self._ai = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
            self._ai.open(dev='Dev1')  # Hepatic Artery Flow Sensor
            self._ai.add_channel(channel_id=3)
            self._ai.start()
        except AIDeviceException as e:
            dlg = wx.MessageDialog(parent=self, message=str(e), caption='AI Device Error', style=wx.OK)
            dlg.ShowModal()
            self._ai = None
            raise e

        try:
            self._ao = NIDAQ_AO()
            self._ao.open(line=1, period_ms=100, dev='Dev3')  # Hepatic Artery BVP Pump
            self._ao.set_dc(0)
        except AODeviceException as e:
            dlg = wx.MessageDialog(parent=self, message=str(e), caption='AO Device Error', style=wx.OK)
            dlg.ShowModal()
            self._ao = None
            raise e

        self._sensor = SensorStream('Flow sensor', 'ml/min', self._ai)
        self.raw = StreamToFile('Raw', None, self._ai.buf_len)
        self.raw.open(LP_CFG.LP_PATH['stream'], f'{self._sensor.name}_raw', self._sensor.params)
        self._sensor.add_strategy(self.raw)

        self.panel_plot = PanelPlotting(self)
        LP_CFG.update_stream_folder()
        self._sensor.open()
        self._sensorplot = SensorPlot(self._sensor, self.panel_plot.axes)
        self._sensorplot.set_strategy(self._sensor.get_file_strategy('Raw'))
        self.panel_plot.add_plot(self._sensorplot)


        self.label_ai = wx.StaticText(self, label=f'Using Analog Input Dev2/ai3')
        self.label_ao = wx.StaticText(self, label=f'Using Analog Output Dev4/ao1')
        self.label_output = wx.StaticText(self, label='Analog Output is xxx')

        self.label_desired_output = wx.StaticText(self, label='Desired Output')
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=1.0, initial=0.5, inc=self._inc)
        self.spin_desired_output.Digits = 3

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
            self._sensor.start()
            self._ao.start()
            self.btn_stop.SetLabel('Stop')
            self.update_output()
            self.timer_flow_adjust.Start(5000, wx.TIMER_CONTINUOUS)
        else:
            self._ao.halt()
            self._sensor.stop()
            self._sensor.hw.remove_channel(3)
            self.btn_stop.SetLabel('Start')
            self.timer_flow_adjust.Stop()

    def OnTimer(self, event):
        if event.GetId() == self.timer_flow_adjust.GetId():
            self.update_output()

    def update_output(self):
        t, flow = self._sensor.get_file_strategy('Raw').retrieve_buffer(0, 1)
        if not flow == []:
            print(f'flow is {flow}, t is {t}')
            flow = flow[0]
            self.pid.setpoint = self.spin_desired_output.GetValue()
            new_val = self.pid(flow)
            self._ao.set_dc(new_val)
            self.label_output.SetLabel(f'Analog output is {new_val:.3f}')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelTestMaintainFlow(self)


class MyTestApp(wx.App):
    def OnInit(self):
        try:
            frame = TestFrame(None, wx.ID_ANY, "")
        except (AIDeviceException, AODeviceException) as e:
            return False
        else:
            self.SetTopWindow(frame)
            frame.Show()
            return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
