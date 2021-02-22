# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for initiating syringe injections based on pressure/flow conditions
"""
import wx

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
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
        self._inc = 0.025

        self._ao = NIDAQ_AO()
        self._ao.open(period_ms=100, dev=dev, line=line)
        self._ao.set_dc(0)

        wx.Panel.__init__(self, parent, -1)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.label_cal_pt1 = wx.StaticText(self, label="Calibration Pt 1")
        self.spin_cal_pt1 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=self._inc)
        self.label_cal_pt2 = wx.StaticText(self, label="Calibration Pt 2")
        self.spin_cal_pt2 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=self._inc)
        self.label_cal_pt1_val = wx.StaticText(self, label='No reading')
        self.label_cal_pt2_val = wx.StaticText(self, label='No reading')
        self.btn_cal_pt1 = wx.Button(self, label='Read Cal Pt 1')
        self.btn_cal_pt2 = wx.Button(self, label='Read Cal Pt 2')
        self.btn_calibrate = wx.Button(self, label='Calibrate')
        self.btn_reset_cal = wx.Button(self, label='Reset Cal')
        self.btn_save_settings = wx.Button(self, label='Save Settings')
        self.btn_load_settings = wx.Button(self, label='Load Settings')
        self.btn_start_calibration = wx.ToggleButton(self, label='Start Calibration')

        self.label_desired_output = wx.StaticText(self, label='Desired Output')
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=100, initial=50, inc=self._inc)

        self.label_tolerance = wx.StaticText(self, label='Tolerance (mmHg)')
        self.spin_tolerance = wx.SpinCtrl(self, min=0, max=100, initial=10)

        self.label_increment = wx.StaticText(self, label='Voltage Increment')
        self.spin_increment = wx.SpinCtrlDouble(self, min=0, max=1, initial=0, inc=0.01)

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.panel_plot = PanelPlotting(self)
        self.panel_plot.add_sensor(self._sensor)
        LP_CFG.update_stream_folder()
        self._sensor.open(LP_CFG.LP_PATH['stream'])

        self.__do_layout()
        self.__set_bindings()

        self._sensor.start()

        self.timer_pressure_adjust = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_save_settings, flags)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_settings, flags)
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
        sizer.Add(self.btn_start_calibration)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_desired_output, flags)
        sizer.Add(self.spin_desired_output, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.label_tolerance, flags)
        sizer.Add(self.spin_tolerance, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.label_increment, flags)
        sizer.Add(self.spin_increment, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.btn_stop, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        self.sizer.Add(self.panel_plot, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_start_calibration.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartCalibration)
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)
        self.btn_save_settings.Bind(wx.EVT_BUTTON, self.OnSaveSettings)
        self.btn_load_settings.Bind(wx.EVT_BUTTON, self.OnLoadSettings)
        self.btn_cal_pt1.Bind(wx.EVT_BUTTON, self.OnCalPt1)
        self.btn_cal_pt2.Bind(wx.EVT_BUTTON, self.OnCalPt2)
        self.btn_calibrate.Bind(wx.EVT_BUTTON, self.OnCalibrate)
        self.btn_reset_cal.Bind(wx.EVT_BUTTON, self.OnResetCalibration)

    def OnStartCalibration(self, evt):
        state = self.btn_start_calibration.GetLabel()
        if state == 'Start Calibration':
            self.btn_stop.Enable(False)
            self._sensor.hw.open(dev='Dev1', line=0)  # HA Pressure Sensor
            self._sensor.hw.start()
            self.btn_start_calibration.SetLabel('Stop Calibration')
        else:
            self.btn_stop.Enable(True)
            self._sensor.hw.stop()
            self._sensor.hw.close()
            self.btn_start_calibration.SetLabel('Start Calibration')

    def OnStartStop(self, evt):
        state = self.btn_stop.GetLabel()
        if state == 'Start':
            self.btn_start_calibration.Enable(False)
            self._sensor.hw.open(dev='Dev1', line=0)  # HA Pressure Sensor
            self._sensor.hw.start()
            self.btn_stop.SetLabel('Stop')
            self.timer_pressure_adjust.Start(1000, wx.TIMER_CONTINUOUS)
        else:
            self.btn_start_calibration.Enable(True)
            self._sensor.hw.stop()
            self._sensor.hw.close()
            self.btn_stop.SetLabel('Start')
            self.timer_pressure_adjust.Stop()
            self._ao.close()
            self._ao.halt()

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
        section = LP_CFG.get_hwcfg_section('HA')
        section['CalPt1_Target'] = f'{self.spin_cal_pt1.GetValue():.3f}'
        section['CalPt1_Reading'] = self.label_cal_pt1_val.GetLabel()
        section['CalPt2_Target'] = f'{self.spin_cal_pt2.GetValue():.3f}'
        section['CalPt2_Reading'] = self.label_cal_pt2_val.GetLabel()
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadSettings(self, evt):
        section = LP_CFG.get_hwcfg_section('HA')
        self.spin_cal_pt1.SetValue(float(section['CalPt1_Target']))
        self.label_cal_pt1_val.SetLabel(section['CalPt1_Reading'])
        self.spin_cal_pt2.SetValue(float(section['CalPt2_Target']))
        self.label_cal_pt2_val.SetLabel(section['CalPt2_Reading'])

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
            sizer.Add(PanelTestPressure(self, sensor, name=sensor.name, dev=pump[0], line=pump[1]), 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self.pressure_sensors:
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
