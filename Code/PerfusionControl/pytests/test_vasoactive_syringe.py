# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for initiating syringe injections based on pressure/flow conditions
"""
import wx

from pyHardware.PHDserial import PHDserial
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG

class PanelTestVasoactiveSyringe(wx.Panel):
    def __init__(self, parent, sensor, name):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._inc = 1.0

        wx.Panel.__init__(self, parent, -1)

        syringe_list = 'Phenylephrine, Epoprostenol'

        self._syringe_vasodilator = PHDserial()
        self._syringe_vasodilator.open('COM11', 9600)
        self.ResetSyringe(self._syringe_vasodilator)
        self.syringe_configuration(self._syringe_vasodilator)

        self._syringe_vasoconstrictor = PHDserial()
        self._syringe_vasoconstrictor.open('COM4', 9600)
        self.ResetSyringe(self._syringe_vasoconstrictor)
        self.syringe_configuration(self._syringe_vasoconstrictor)

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

        self.timer_injection = wx.Timer(self, id=0)
        self.Bind(wx.EVT_TIMER, self.OnTimer, id=0)

        self.timer_vasodilator_injection = wx.Timer(self, id=1)
        self.Bind(wx.EVT_TIMER, self.OnVasodilatorInjectionTimer, id=1)

        self.timer_vasoconstrictor_injection = wx.Timer(self, id=2)
        self.Bind(wx.EVT_TIMER, self.OnVasoconstrictorInjectionTimer, id=2)

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
            self.timer_injection.Start(10000, wx.TIMER_CONTINUOUS)
        else:
            self.btn_stop.SetLabel('Start')
            self.timer_injection.Stop()

    def OnTimer(self, event):
        if event.GetId() == self.timer_injection.GetId():
            if self._syringe_vasodilator.reset:
                self.ResetSyringe(self._syringe_vasodilator)
                self._syringe_vasodilator.reset = False
            if self._syringe_vasoconstrictor.reset:
                self.ResetSyringe(self._syringe_vasoconstrictor)
                self._syringe_vasoconstrictor.reset = False
            self.check_for_injection()

    def OnVasodilatorInjectionTimer(self, event):
        if event.GetId() == self.timer_vasodilator_injection.GetId():
            self._syringe_vasodilator.cooldown = False
            self.timer_vasodilator_injection.Stop()

    def OnVasoconstrictorInjectionTimer(self, event):
        if event.GetId() == self.timer_vasoconstrictor_injection.GetId():
            self._syringe_vasoconstrictor.cooldown = False
            self.timer_vasoconstrictor_injection.Stop()

    def ResetSyringe(self, syringe):
        syringe.reset_infusion_volume()
        syringe.reset_target_volume()

    def syringe_configuration(self, syringe):
        syringe.set_syringe_manufacturer_size('bdp', '60 ml')
        syringe.set_infusion_rate(30, 'ml/min')

    def check_for_injection(self):
        flow = float(self._sensor.get_current())
        min_flow = float(self.spin_min_flow.GetValue())
        max_flow = float(self.spin_max_flow.GetValue())
        tol = float(self.spin_tolerance.GetValue())
        if flow > (max_flow + tol):
            if not self._syringe_vasoconstrictor.cooldown:
                flow_diff = flow - (max_flow + tol)
                injection_volume = flow_diff / 10
                self.injection(self._syringe_vasoconstrictor, 'phenylephrine', flow, injection_volume, direction='high')
                self.timer_vasoconstrictor_injection.Start(30000, wx.TIMER_CONTINUOUS)
            else:
                print(f'Flow is {flow:.2f} , which is too high; however, vasoconstrictor injections are currently frozen')
        elif flow < (min_flow - tol):
            if not self._syringe_vasodilator.cooldown:
                flow_diff = (min_flow - tol) - flow
                injection_volume = flow_diff / 10
                self.injection(self._syringe_vasodilator, 'epoprostenol', flow, injection_volume, direction='low')
                self.timer_vasodilator_injection.Start(30000, wx.TIMER_CONTINUOUS)
            else:
                print(f'Flow is {flow:.2f} , which is too low; however, vasodilator injections are currently frozen')
        else:
            print(f'Flow is {flow:.2f} , which is in range')

    def injection(self, syringe, name, flow, volume, direction):
        print(f'Flow is {flow:.2f} , which is too {direction}; injecting {volume:.2f} mL of {name}')
        syringe.set_target_volume(volume, 'ml')
        syringe.infuse()
        syringe.reset = True
        syringe.cooldown = True


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
