# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for initiating syringe injections based on pressure/flow conditions
"""
import wx

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.syringe_timer import SyringeTimer
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG

class PanelTestVasoactiveSyringe(wx.Panel):
    def __init__(self, parent, sensor, name):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._inc = 1.0
        self._vasodilator_injection = None
        self._vasoconstrictor_injection = None

        wx.Panel.__init__(self, parent, -1)

        syringe_list = 'Phenylephrine, Epoprostenol'

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_min_flow = wx.StaticText(self, label='Minimum Flow: ')
        self.spin_min_flow = wx.SpinCtrlDouble(self, min=0, max=1000, initial=0.0, inc=self._inc)
        self.label_max_flow = wx.StaticText(self, label='Maximum Flow: ')
        self.spin_max_flow = wx.SpinCtrlDouble(self, min=0, max=1000, initial=50, inc=self._inc)

        self.label_tolerance = wx.StaticText(self, label='Tolerance (mL/min): ')
        self.spin_tolerance = wx.SpinCtrl(self, min=0, max=20, initial=0)

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.label_syringes = wx.StaticText(self, label='Syringes In Use: %s' % syringe_list)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_syringes, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_min_flow, flags)
        sizer.Add(self.spin_min_flow, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_max_flow, flags)
        sizer.Add(self.spin_max_flow, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_tolerance, flags)
        sizer.Add(self.spin_tolerance, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
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
            self.btn_stop.SetLabel('Stop')
            self._vasoconstrictor_injection = SyringeTimer(self, 'Phenylephrine', 'COM4', 9600, self.spin_max_flow.GetValue(), self.spin_tolerance.GetValue(), self._sensor)
            self._vasodilator_injection = SyringeTimer(self, 'Epoprostenol', 'COM11', 9600, self.spin_min_flow.GetValue(), self.spin_tolerance.GetValue(), self._sensor)
        else:
            self._vasoconstrictor_injection.stop_injection_timer()
            self._vasodilator_injection.stop_injection_timer()
            self.btn_stop.SetLabel('Start')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Flow Sensor', 'mL/min', self.acq)
        sizer.Add(PanelAI(self, self.sensor, self.sensor.name), 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(PanelTestVasoactiveSyringe(self, self.sensor, 'Vasoactive Syringe Testing'), 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.sensor.stop()
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
