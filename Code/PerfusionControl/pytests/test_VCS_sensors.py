# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Test app for testing how to maintain flow
"""
import wx

from pyPerfusion.panel_VCS import TestFrame as VCSTestFrame

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG

class PanelTestVCSSensors(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        self._inc = 0.1

        self._ai = NIDAQ_AI(line=4, period_ms=100, volts_p2p=5, volts_offset=2.5, dev='Dev1')
        self._ao = NIDAQ_AO()
        self._ao.open(line=1, period_ms=100, dev='Dev1')
        self._sensor = SensorStream('Flow sensor', 'ml/min', self._ai)


        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.label_ai = wx.StaticText(self, label=f'Using Analog Input {self._ai._devname}')
        self.label_ao = wx.StaticText(self, label=f'Using Analog Output {self._ao._devname}')
        self.label_output = wx.StaticText(self, label='Analog Output is xxx')

        self.label_desired_output = wx.StaticText(self, label='Desired Output')
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=2.5, inc=self._inc)
        self.spin_desired_output.Digits = 3

        self.label_tolerance = wx.StaticText(self, label='Tolerance (%)')
        self.spin_tolerance = wx.SpinCtrl(self, min=0, max=100, initial=10)

        self.panel_plot = PanelPlotting(self)
        self.panel_plot.add_sensor(self._sensor)
        LP_CFG.update_stream_folder()
        self._sensor.open(LP_CFG.LP_PATH['stream'])
        self._ao.set_dc(0)

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

        self.timer_flow_adjust = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)


    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        self.sizer.Add(self.label_ai)
        self.sizer.Add(self.label_ao)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_desired_output, flags)
        sizer.Add(self.spin_desired_output, flags)
        sizer.Add(self.btn_stop, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_tolerance, flags)
        sizer.Add(self.spin_tolerance, flags)
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
            self._ao.start()
            self._sensor.start()
            self.btn_stop.SetLabel('Stop')
            self.update_output()
            self.timer_flow_adjust.Start(1000, wx.TIMER_CONTINUOUS)
        else:
            self._sensor.stop()
            self.btn_stop.SetLabel('Stop')
            self.timer_flow_adjust.Stop()

    def OnTimer(self, event):
        if event.GetId() == self.timer_flow_adjust.GetId():
            self.update_output()

    def update_output(self):
        flow = self._sensor.get_current()
        desired = self.spin_desired_output.GetValue()
        tol = self.spin_tolerance.GetValue() / 100
        dev = abs(desired - flow)
        print(f'Flow is {flow:.3f}, desired is {desired:.3f}')
        print(f'Deviation is {dev}, tol is {tol}')
        if dev > tol:
            if flow < desired:
                new_val = self._ao.volts_offset + self._inc
            else:
                new_val = self._ao.volts_offset - self._inc
            self._ao.set_dc(new_val)
            self.label_output.SetLabel(f'Analog output is {new_val:.3f}')

class SensorTestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelTestVCSSensors(self)

class MyTestApp(wx.App):
    def OnInit(self):
        frameVCS = VCSTestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frameVCS)
        frameVCS.Show()
        frameSensors = SensorTestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frameSensors)
        frameSensors.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()

