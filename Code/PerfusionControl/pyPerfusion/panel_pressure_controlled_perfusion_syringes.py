# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for adjusting pump speeds to maintain desired perfusion pressures
"""
import wx
import logging
import pyPerfusion.utils as utils

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.pyPump11Elite import Pump11Elite
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.panel_auto_syringe_injections import PanelSyringe
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy

class PanelPressureFlowControl(wx.Panel):
    def __init__(self, parent, main_sensor, corresponding_sensor, pump, name, pumpname):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._main_sensor = main_sensor
        self._corresponding_sensor = corresponding_sensor
        self._pump = pump
        self._name = name
        self._pumpname = pumpname

        section = PerfusionConfig.read_section('hardware', self._pumpname)
        self.dev = section['Device']
        self.line = section['LineName']
        self.desired = float(section['desired'])
        self.tolerance = float(section['tolerance'])
        self.increment = float(section['increment'])
        try:
            self.divisor = float(section['divisor'])
        except KeyError:
            self.divisor = None

        try:
            section = PerfusionConfig.read_section('hardware', self._corresponding_sensor.name)
            self.upperlimit = float(section['upperlimit'])
        except KeyError:
            self.upperlimit = None

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.label_desired_output = wx.StaticText(self, label='Desired ' + self._name)
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=500, initial=self.desired, inc=0.1)
        self.btn_update_desired = wx.Button(self, label='Update Desired Parameter')

        self.label_tolerance = wx.StaticText(self, label='Tolerance (' + self._main_sensor._unit_str + ')')
        self.spin_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=self.tolerance, inc=0.1)
        self.btn_update_tolerance = wx.Button(self, label='Update Tolerance')

        self.label_increment = wx.StaticText(self, label='Voltage Increment')
        self.spin_increment = wx.SpinCtrlDouble(self, min=0, max=1, initial=self.increment, inc=0.001)
        self.btn_update_increment = wx.Button(self, label='Update Voltage Increment')

        if self.divisor:
            self.label_divisor = wx.StaticText(self, label='Peak-to-Peak Divisor')
            self.spin_divisor = wx.SpinCtrlDouble(self, min=0, max=100, initial=self.divisor, inc=0.1)
            self.btn_update_divisor = wx.Button(self, label='Update Divisor')

        if self.upperlimit:
            self.label_corresponding_limit = wx.StaticText(self, label='Maximum Allowable ' + self._corresponding_sensor.name)
            self.spin_corresponding_limit = wx.SpinCtrlDouble(self, min=0, max=1000, initial=self.upperlimit, inc=1)
            self.btn_update_corresponding_limit = wx.Button(self, label='Update Upper Limit')

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

        self.timer_adjust = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_label.Add(self.label_desired_output, flags)
        self.sizer_label.Add(self.spin_desired_output, flags)
        self.sizer_label.Add(self.btn_update_desired, flags)

        self.sizer_tol = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_tol.Add(self.label_tolerance, flags)
        self.sizer_tol.Add(self.spin_tolerance, flags)
        self.sizer_tol.Add(self.btn_update_tolerance, flags)

        self.sizer_increment = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_increment.Add(self.label_increment, flags)
        self.sizer_increment.Add(self.spin_increment, flags)
        self.sizer_increment.Add(self.btn_update_increment, flags)

        if self.divisor:
            self.sizer_divisor = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer_divisor.Add(self.label_divisor, flags)
            self.sizer_divisor.Add(self.spin_divisor, flags)
            self.sizer_divisor.Add(self.btn_update_divisor, flags)

        if self.upperlimit:
            self.sizer_corresponding_limit = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer_corresponding_limit.Add(self.label_corresponding_limit, flags)
            self.sizer_corresponding_limit.Add(self.spin_corresponding_limit, flags)
            self.sizer_corresponding_limit.Add(self.btn_update_corresponding_limit, flags)

        sizer = wx.GridSizer(cols=1)
        sizer.Add(self.sizer_label)
        sizer.Add(self.sizer_tol)
        sizer.Add(self.sizer_increment, flags)
        sizer.Add(self.btn_stop, flags)
        if self.divisor:
            sizer.Add(self.sizer_divisor, flags)
        if self.upperlimit:
            sizer.Add(self.sizer_corresponding_limit)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_update_desired.Bind(wx.EVT_BUTTON, self.OnDesired)
        self.btn_update_tolerance.Bind(wx.EVT_BUTTON, self.OnTolerance)
        self.btn_update_increment.Bind(wx.EVT_BUTTON, self.OnIncrement)
        if self.divisor:
            self.btn_update_divisor.Bind(wx.EVT_BUTTON, self.OnDivisor)
        if self.upperlimit:
            self.btn_update_corresponding_limit.Bind(wx.EVT_BUTTON, self.OnCorrespondingLimit)
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)

    def OnDesired(self, evt):
        self.desired = self.spin_desired_output.GetValue()

    def OnTolerance(self, evt):
        self.tolerance = self.spin_tolerance.GetValue()

    def OnIncrement(self, evt):
        self.increment = self.spin_increment.GetValue()

    def OnDivisor(self, evt):
        self.divisor = self.spin_divisor.GetValue()

    def OnCorrespondingLimit(self, evt):
        self.upperlimit = self.spin_corresponding_limit.GetValue()

    def OnStartStop(self, evt):
        state = self.btn_stop.GetLabel()
        if state == 'Start':
            self._pump.open(period_ms=100, dev=self.dev, line=self.line)
            self._pump.set_dc(1.5)
            self.desired = self.spin_desired_output.GetValue()
            self.tolerance = self.spin_tolerance.GetValue()
            self.increment = self.spin_increment.GetValue()
            if self.divisor:
                self.divisor = self.spin_divisor.GetValue()
            if self.upperlimit:
                self.upperlimit = self.spin_corresponding_limit.GetValue()
            self.timer_adjust.Start(3000, wx.TIMER_CONTINUOUS)
            self.btn_stop.SetLabel('Stop')
        else:
            self.timer_adjust.Stop()
            self._pump.set_dc(0)
            self._pump.close()
            self._pump.halt()
            self.btn_stop.SetLabel('Start')

    def OnTimer(self, event):
        if event.GetId() == self.timer_adjust.GetId():
            self.update_output()

    def update_output(self):
        if 'Hepatic Artery' in self._main_sensor.name:
            t, value = self._main_sensor.get_file_strategy('StreamRMS').retrieve_buffer(0, 1)
        else:
            t, value = self._main_sensor.get_file_strategy('StreamRaw').retrieve_buffer(0, 1)
        dev = abs(self.desired - value)
        if dev > self.tolerance:
            if value < self.desired:
                new_val = self._pump._volts_offset + self.increment
                if new_val > 5:
                    new_val = 5
                if self.upperlimit:
                    if 'Hepatic Artery' in self._main_sensor.name:
                        t, corresponding_value = self._corresponding_sensor.get_file_strategy('StreamRMS').retrieve_buffer(0, 1)
                    else:
                        t, corresponding_value = self._corresponding_sensor.get_file_strategy('StreamRaw').retrieve_buffer(0, 1)
                    if corresponding_value > self.upperlimit:
                        self._logger.info(f'{self._corresponding_sensor.name} is too high; cannot further increase pump speed')
                        return
            else:
                new_val = self._pump._volts_offset - self.increment
                if new_val < 0:
                    new_val = 0
            if "Hepatic Artery" in self._main_sensor.name and self.divisor:
                peak = (new_val / self.divisor) / 2
                peak_high = None
                peak_low = None
                if (new_val + peak) > 5:
                    peak_high = (5-new_val)
                    peak = peak_high
                if (new_val - peak) < 0:
                    peak_low = new_val
                    peak = peak_low
                if peak_high and peak_low:
                    if peak_high > peak_low:
                        peak = peak_low
                    elif peak_low > peak_high:
                        peak = peak_high
                self._pump.set_sine(2 * peak, new_val, Hz=1)
            else:
                self._pump.set_dc(new_val)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=3)
        ha_sizer = wx.FlexGridSizer(cols=1)
        ha_sizer.AddGrowableRow(0, 2)
        ha_sizer.AddGrowableRow(1, 2)
        pv_sizer = wx.FlexGridSizer(cols=1)
        pv_sizer.AddGrowableRow(0, 2)
        pv_sizer.AddGrowableRow(1, 2)
        ivc_sizer = wx.FlexGridSizer(cols=1)
        ivc_sizer.AddGrowableRow(0, 1)
        ivc_sizer.AddGrowableRow(1, 1)

        self.panels = []

        self.acq =  NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.acq.open(dev='Dev1')
        self.acq.start()

        self.sensors = [SensorStream('Hepatic Artery Pressure', 'mmHg', self.acq), SensorStream('Portal Vein Pressure', 'mmHg', self.acq), SensorStream('Inferior Vena Cava Pressure', 'mmHg', self.acq), SensorStream('Hepatic Artery Flow', 'ml/min', self.acq), SensorStream('Portal Vein Flow', 'ml/min', self.acq), SensorStream('Inferior Vena Cava Flow', 'ml/min', self.acq)]

        self.hepatic_artery_pressure_control = None
        self.portal_vein_flow_control = None
        self.pumps = []

        for sensor in self.sensors:
            raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
            raw.open(PerfusionConfig.get_date_folder(), f'{sensor.name}_raw', sensor.params)
            sensor.add_strategy(raw)
            if 'Hepatic Artery' in sensor.name:
                rms = RMSStrategy('RMS', 50, self.acq.buf_len)
                save_rms = StreamToFile('StreamRMS', None, self.acq.buf_len)
                save_rms.open(PerfusionConfig.get_date_folder(), f'{sensor.name}_rms', sensor.params)
                sensor.add_strategy(rms)
                sensor.add_strategy(save_rms)
            panel = PanelAI(self, sensor, name=sensor.name, strategy='StreamRaw')
            section = PerfusionConfig.read_section('hardware', sensor.name)
            dev = section['Device']
            line = section['LineName']
            self._lgr.debug(f'From {sensor.name}, line is {line}')
            calpt1_target = float(section['CalPt1_Target'])
            calpt1_reading = section['CalPt1_Reading']
            calpt2_target = float(section['CalPt2_Target'])
            calpt2_reading = section['CalPt2_Reading']
            panel._panel_cfg.choice_dev.SetStringSelection(dev)
            panel._panel_cfg.choice_line.SetSelection(int(line))
            panel._panel_cfg.choice_dev.Enable(False)
            panel._panel_cfg.choice_line.Enable(False)
            panel._panel_cfg.panel_cal.spin_cal_pt1.SetValue(calpt1_target)
            panel._panel_cfg.panel_cal.label_cal_pt1_val.SetLabel(calpt1_reading)
            panel._panel_cfg.panel_cal.spin_cal_pt2.SetValue(calpt2_target)
            panel._panel_cfg.panel_cal.label_cal_pt2_val.SetLabel(calpt2_reading)
            if 'Hepatic Artery' in sensor.name:
                ha_sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            elif 'Portal Vein' in sensor.name:
                pv_sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            elif 'Inferior Vena Cava' in sensor.name:
                ivc_sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            sensor.open()
            sensor.start()

        if self.hepatic_artery_pressure_control:
            ha_sizer.Add(self.hepatic_artery_pressure_control, 1, wx.ALL | wx.EXPAND, border=1)

        if self.portal_vein_flow_control:
            pv_sizer.Add(self.portal_vein_flow_control, 1, wx.ALL | wx.EXPAND, border=1)

        if self.epoprostenol_syringe_panel:
            syringe_sizer.Add(self.epoprostenol_syringe_panel, 1, wx.ALL | wx.EXPAND)

        if self.phenylephrine_syringe_panel:
            syringe_sizer.Add(self.phenylephrine_syringe_panel, 1, wx.ALL | wx.EXPAND)

        sizer.Add(ha_sizer, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(pv_sizer, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(ivc_sizer, 1, wx.ALL | wx.EXPAND, border=1)
        #sizer.Add(syringe_sizer, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        if self.portal_vein_flow_control:
            self.portal_vein_flow_control.timer_adjust.Stop()
        if self.hepatic_artery_pressure_control:
            self.hepatic_artery_pressure_control.timer_adjust.Stop()
        for panel in self.panels:
            if not panel:
                pass
            else:
                panel._panel_feedback._syringe_timer.stop_feedback_injections()
        for syringe in self.syringes:
            syringe.stop()
            syringe.close()
        for sensor in self.sensors:
            sensor.stop()
            sensor.close()
            sensor.hw.stop()
            sensor.hw.close()
        for pump in self.pumps:
            pump.set_dc(0)
            pump.close()
            # pump.halt()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging(filename='panel_pressure_controlled_perfusion_syringes')
    app = MyTestApp(0)
    app.MainLoop()
