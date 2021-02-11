# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for initiating syringe injections based on pressure/flow conditions
"""
import wx

from pyPerfusion.panel_Syringe import PanelSyringe
from pyHardware.PHDserial import PHDserial
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG

class PanelTestVasoactiveSyringe(wx.Panel):
    def __init__(self, parent, sensor, name):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._inc = 0.1
        wx.Panel.__init__(self, parent, -1)

        syringe_list = ('Phenylephrine, Epoprostenol')

        self._syringe_vasodilator = PHDserial()
        self._syringe_vasodilator.open('COM11', 9600)
        self._syringe_vasodilator.set_syringe_manufacturer_size('bdp', '60 ml')
        self._syringe_vasodilator.set_infusion_rate(30, 'ml')
        self._syringe_vasodilator.reset_infusion_volume()
        self._syringe_vasodilator.reset_target_volume()

        self._syringe_vasoconstrictor = PHDserial()
        self._syringe_vasoconstrictor.open('COM4', 9600)
        self._syringe_vasoconstrictor.set_syringe_manufacturer_size('bdp', '60 ml')
        self._syringe_vasoconstrictor.set_infusion_rate(30, 'ml')
        self._syringe_vasoconstrictor.reset_infusion_volume()
        self._syringe_vasoconstrictor.reset_target_volume()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.label_cal_pt1 = wx.StaticText(self, label="Calibration Pt 1")
        self.spin_cal_pt1 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.label_cal_pt2 = wx.StaticText(self, label="Calibration Pt 2")
        self.spin_cal_pt2 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.spin_cal_pt1.Digits = 3
        self.spin_cal_pt2.Digits = 3
        self.label_cal_pt1_val = wx.StaticText(self, label='No reading')
        self.label_cal_pt2_val = wx.StaticText(self, label='No reading')
        self.btn_cal_pt1 = wx.Button(self, label='Read Cal Pt 1')
        self.btn_cal_pt2 = wx.Button(self, label='Read Cal Pt 2')
        self.btn_calibrate = wx.Button(self, label='Calibrate')
        self.btn_reset_cal = wx.Button(self, label='Reset Cal')
        self.btn_save_settings = wx.Button(self, label='Save Settings')
        self.btn_load_settings = wx.Button(self, label='Load Settings')

        self.label_min_flow = wx.StaticText(self, label='Minimum Flow: ')
        self.spin_min_flow = wx.SpinCtrlDouble(self, min=0, max=400, initial=0.0, inc=self._inc)
        self.spin_min_flow.Digits = 3
        self.label_max_flow = wx.StaticText(self, label='Maximum Flow: ')
        self.spin_max_flow = wx.SpinCtrlDouble(self, min=0, max=400, initial=100.0, inc=self._inc)
        self.spin_max_flow.Digits = 3

        self.label_tolerance = wx.StaticText(self, label='Tolerance (mmHg): ')
        self.spin_tolerance = wx.SpinCtrl(self, min=0, max=20, initial=10)

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.label_syringes = wx.StaticText(self, label='Syringes In Use: %s' % syringe_list)

        self.panel_plot = PanelPlotting(self)
        self.panel_plot.add_sensor(self._sensor)
        LP_CFG.update_stream_folder()
        self._sensor.open(LP_CFG.LP_PATH['stream'])

        self.__do_layout()
        self.__set_bindings()

        self.timer_injection = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self._sensor.start()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_save_settings, flags)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_settings, flags)
        self.sizer.AddSpacer(10)
        self.sizer.Add(sizer)

        sizer = wx.GridSizer(cols=4)
        sizer.Add(self.label_cal_pt1, flags)
        sizer.Add(self.spin_cal_pt1, flags)
        sizer.Add(self.btn_cal_pt1, flags)
        sizer.Add(self.label_cal_pt1_val, flags)
        sizer.Add(self.label_cal_pt2, flags)
        sizer.Add(self.spin_cal_pt2, flags)
        sizer.Add(self.btn_cal_pt2, flags)
        sizer.Add(self.label_cal_pt2_val, flags)
        sizer.Add(self.btn_calibrate, flags)
        sizer.Add(self.btn_reset_cal, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_syringes, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_min_flow, flags)
        sizer.Add(self.spin_min_flow, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.label_max_flow, flags)
        sizer.Add(self.spin_max_flow, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.label_tolerance, flags)
        sizer.Add(self.spin_tolerance, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.btn_stop, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        self.sizer.Add(self.panel_plot, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)
        self.btn_save_settings.Bind(wx.EVT_BUTTON, self.OnSaveSettings)
        self.btn_load_settings.Bind(wx.EVT_BUTTON, self.OnLoadSettings)
        self.btn_cal_pt1.Bind(wx.EVT_BUTTON, self.OnCalPt1)
        self.btn_cal_pt2.Bind(wx.EVT_BUTTON, self.OnCalPt2)
        self.btn_calibrate.Bind(wx.EVT_BUTTON, self.OnCalibrate)
        self.btn_reset_cal.Bind(wx.EVT_BUTTON, self.OnResetCalibration)

    def OnStartStop(self, evt):
        state = self.btn_stop.GetLabel()
        if state == 'Start':
            self._sensor.hw.open(dev='Dev1', line=0)  # HA Pressure Sensor
            self._sensor.hw.start()
            self.btn_stop.SetLabel('Stop')
            self.check_for_injection()
            self.timer_injection.Start(1000000, wx.TIMER_CONTINUOUS)
        else:
            self._sensor.hw.stop()
            self._sensor.hw.close()
            self.btn_stop.SetLabel('Start')
            self.timer_injection.Stop()

    def OnCalPt1(self, evt):
        val = self._sensor.get_current()
        self.label_cal_pt1_val.SetLabel(f'{val:.3f}')

    def OnCalPt2(self, evt):
        val = self._sensor.get_current()
        self.label_cal_pt2_val.SetLabel(f'{val:.3f}')

    def OnCalibrate(self, evt):
        low_pt = self.spin_cal_pt1.GetValue()
        low_read = float(self.label_cal_pt1_val.GetLabel())
        high_pt = self.spin_cal_pt2.GetValue()
        high_read = float(self.label_cal_pt2_val.GetLabel())
        self._sensor.hw.set_2pt_cal(low_pt, low_read, high_pt, high_read)

    def OnResetCalibration(self, evt):
        self._sensor.hw.set_2pt_cal(0, 0, 1, 1)
        self.spin_cal_pt1.SetValue(0)
        self.spin_cal_pt2.SetValue(1)
        self.label_cal_pt1_val.SetLabel('0')
        self.label_cal_pt2_val.SetLabel('1')

    def OnSaveSettings(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['CalPt1_Target'] = f'{self.spin_cal_pt1.GetValue():.3f}'
        section['CalPt1_Reading'] = self.label_cal_pt1_val.GetLabel()
        section['CalPt2_Target'] = f'{self.spin_cal_pt2.GetValue():.3f}'
        section['CalPt2_Reading'] = self.label_cal_pt2_val.GetLabel()
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadSettings(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self.spin_cal_pt1.SetValue(float(section['CalPt1_Target']))
        self.label_cal_pt1_val.SetLabel(section['CalPt1_Reading'])
        self.spin_cal_pt2.SetValue(float(section['CalPt2_Target']))
        self.label_cal_pt2_val.SetLabel(section['CalPt2_Reading'])

    def OnTimer(self, event):
        if event.GetId() == self.timer_injection.GetId():
            self._syringe_vasodilator.reset_infusion_volume()
            self._syringe_vasodilator.reset_target_volume()
            self._syringe_vasoconstrictor.reset_infusion_volume()
            self._syringe_vasoconstrictor.reset_target_volume()
            self.check_for_injection()

    def check_for_injection(self):
        pressure = self._sensor.get_current()
        print(pressure)
        min_pressure = self.spin_min_flow.GetValue()
        max_pressure = self.spin_max_flow.GetValue()
        tol = self.spin_tolerance.GetValue()
        if pressure > (max_pressure + tol):
            print(f'Pressure is {pressure:.3f} , which is too high')
            pressure_diff = pressure - (max_pressure + tol)
            injection_volume = pressure_diff / 5
            self._syringe_vasoconstrictor.set_target_volume(injection_volume, 'ml')
            self._syringe_vasoconstrictor.infuse()
        elif pressure < (min_pressure - tol):
            print(f'Pressure is {pressure:.3f} , which is too low')
            pressure_diff = (min_pressure - tol) - pressure
            injection_volume = pressure_diff / 5
            self._syringe_vasodilator.set_target_volume(injection_volume, 'ml')
            self._syringe_vasodilator.infuse()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.ai = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Pressure Sensor', 'mmHg', self.ai)
        self.panel = PanelTestVasoactiveSyringe(self, self.sensor, 'Vasoactive Syringe Testing')
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
    app = MyTestApp(0)
    app.MainLoop()
